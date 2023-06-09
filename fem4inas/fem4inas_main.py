"""FEM4INAS main"""
import fem4inas.drivers
from fem4inas.preprocessor.config import Config
from fem4inas.preprocessor.utils import initialise_config
from fem4inas.drivers.driver import Driver
from fem4inas.preprocessor.solution import Solution

def main(input_file: str = None,
         input_dict: dict = None,
         input_obj: Config = None,
         return_driver: bool = False) -> Solution | Driver:
    """Main ``FEM4INAS`` routine


    Parameters
    ----------
    input_file : str
        Path to YAML input file
    input_dict : dict
        Alternatively, dictionary with the settings to be loaded into
        the Config object.
    input_obj : Config
        Alternatively input the Config object directly.

    Returns
    -------
    Solution
        Data object with the numerical solution saved along the
        process.

    """

    config = initialise_config(input_file, input_dict, input_obj)
    Driver = fem4inas.drivers.factory(config.driver.typeof)
    driver = Driver(config)
    driver.pre_simulation()
    driver.run_case()

    if return_driver:  # return driver object for inspection
        return driver
    else:  # just return the solution data
        return driver.sol

