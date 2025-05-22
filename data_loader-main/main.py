from src.sdm.sdm_pipeline import SDM_PIPELINE
from definitions import CONFIG_DIR
from src.utils.utilities import config_param, get_logger
import time
def run_pipeline():
    start_time = time.time()
    print('Run pipeline')
    sdm_config = f'{CONFIG_DIR}/sdm_config.yaml'
    data_config = config_param(config_file=sdm_config, field='data_pipe')
    pipel = SDM_PIPELINE(schedule=data_config['schedule'])

    tbl_list = data_config['table_list'].replace(' ', '').split(',')
    for tbl in tbl_list:
        print(tbl)
        pipel.load_mtr_vs(template=data_config['template'],
                          raw_tbl=tbl, prodOnly=data_config['prod_only'])

    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    run_pipeline()
