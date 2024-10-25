from distributed_learning_simulation import (
    CentralizedAlgorithmFactory,
    FedAVGAlgorithm,
    NNADQClientEndpoint,
    NNADQServerEndpoint,
    StochasticQuantClientEndpoint,
    StochasticQuantServerEndpoint,
)

from .server import FedOBDServer
from .worker import FedOBDWorker

CentralizedAlgorithmFactory.register_algorithm(
    algorithm_name="fed_obd",
    client_cls=FedOBDWorker,
    server_cls=FedOBDServer,
    client_endpoint_cls=NNADQClientEndpoint,
    server_endpoint_cls=NNADQServerEndpoint,
    algorithm_cls=FedAVGAlgorithm,
)

CentralizedAlgorithmFactory.register_algorithm(
    algorithm_name="fed_obd_sq",
    client_cls=FedOBDWorker,
    server_cls=FedOBDServer,
    client_endpoint_cls=StochasticQuantClientEndpoint,
    server_endpoint_cls=StochasticQuantServerEndpoint,
    algorithm_cls=FedAVGAlgorithm,
)
