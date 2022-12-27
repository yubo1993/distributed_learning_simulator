from typing import Any

import gevent.lock
from cyy_naive_lib.log import get_logger
from cyy_torch_toolbox.metric_visualizers.metric_logger import MetricLogger
from cyy_torch_toolbox.ml_type import ModelExecutorHookPoint
from cyy_torch_toolbox.trainer import Trainer
from executor import Executor


class Worker(Executor):
    semaphore = gevent.lock.BoundedSemaphore(value=1)

    def __init__(
        self,
        task_id: Any,
        worker_id: int,
        trainer: Trainer,
        **kwargs: dict,
    ):
        name = f"worker {worker_id}"
        if task_id is not None:
            name = f"worker {worker_id} of {task_id}"
        super().__init__(name=name, **kwargs)
        self.__worker_id = worker_id
        self.__trainer = trainer
        self.__trainer.visualizer.disable()
        self._round_num = 0
        self._force_stop = False

    @property
    def worker_id(self):
        return self.__worker_id

    @property
    def trainer(self):
        return self.__trainer

    def _offload_from_memory(self):
        self.__trainer.offload_from_gpu()

    def _release_semaphore(self) -> None:
        if self.config.offload_memory:
            self._offload_from_memory()
        super()._release_semaphore()

    def _before_training(self):
        self._force_stop = False
        self.trainer.set_device(
            self._get_device(
                lock_callback=lambda: self.trainer.append_named_hook(
                    ModelExecutorHookPoint.AFTER_BATCH,
                    "release_device_lock",
                    self._release_device_lock,
                )
            )
        )

    def _stopped(self) -> bool:
        return self._round_num > self.config.round or self._force_stop

    def start(self, **kwargs):
        first_training: bool = True
        self._round_num = 1
        while True:
            # in case worker changes round number
            if self._stopped():
                break
            self._acquire_semaphore()
            if first_training:
                self._before_training()
                first_training = False
            else:
                self.trainer.disable_logger()
            MetricLogger.prefix = "round:" + str(self._round_num) + ","
            self.trainer.visualizer.set_session_name(f"round_{self._round_num}")
            self.trainer.train(**kwargs)
            self._release_semaphore()
            self._round_num += 1
        get_logger().debug("close endpoint")
        self._endpoint.close()
        get_logger().debug("finish worker %s", self.worker_id)
