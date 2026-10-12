# Created by aaronkueh at 7/8/24
import time

from definitions import CONFIG_DIR
from src.utils.read_thing import GetThings
from src.utils.utilities import config_param, get_logger
from src.utils.sdm_client import pg_client
from src.sdm.sdm_connect import SDMConnect
from src.sdm.sdm_tbl import sie_mtr_raw, sew_mtr_raw, aircon_tbl
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.sdm.bulk_loader import upsert_dataframe
from sqlalchemy import inspect

logger = get_logger(__name__)


class SDM_PIPELINE(object):
    def __init__(self, schedule=True):
        self.twx_config = f'{CONFIG_DIR}/api_config.yaml'
        self.sdm_config = f'{CONFIG_DIR}/sdm_config.yaml'
        self.get_things = GetThings(config_file=self.twx_config, templateFromConfig=False)
        self.sdm = SDMConnect(config_file=self.sdm_config)
        self.templateName = str(config_param(config_file=self.twx_config,
                                             field='template_name')).replace(' ', '').split(',')
        db_config = config_param(config_file=self.sdm_config, field='sdm_db')
        self.load_data = config_param(config_file=self.sdm_config, field='load_data')
        self.eng, self.conn, self.sess, self.insp = pg_client(config=db_config)
        self.schema = db_config['schema']
        self.now = datetime.now()
        if schedule:
            end = datetime.today()
            start = end - timedelta(days=1)
            self.start_date = start.strftime('%Y-%m-%d')
            self.end_date = end.strftime('%Y-%m-%d')
            self.start_str = start.strftime('%Y%m%d')
            self.end_str = end.strftime('%Y%m%d')
        else:
            self.start_date = self.load_data['start_date']
            self.end_date = self.load_data['end_date']
            self.start_str = self.start_date.strftime('%Y%m%d')
            self.end_str = self.end_date.strftime('%Y%m%d')
        print('schedule', schedule)
        print('start and end date', self.start_date, self.end_date)
        self.table_name = self.load_data['table_name']
        self.maxItems = 86400
        self.project = config_param(config_file=self.twx_config, field='project')

    def gen_date(self, startDate: str):
        """
        Read start date and end date range from config
        Remove non production date according to MES production date for given cell
        Args:
            startDate: Cell ID
        Returns:
        """
        date_objects = datetime.strptime(startDate, '%Y%m%d')
        date_s = (date_objects - timedelta(days=1)).strftime('%Y-%m-%d')  # 7am SGT = 11pm UTC previous day
        date_e = date_objects.strftime('%Y-%m-%d')
        self.start_date = date_s + self.load_data['start_time']
        self.end_date = date_e + self.load_data['end_time']
        # self.maxItems = int((self.end_date - self.start_date).days * 86400)
        print('new date', self.start_date, self.end_date)

    def get_thing_vs(self, propertyList: list, thing: str, cell: str, fac_no: int) -> pd.DataFrame:
        """
        Extract thing value stream raw data based on properties, start date and end date
        Args:
            propertyList: List of properties based on thing's template from config
            thing: Thing name
            cell: Cell ID
            fac_no: facility number
        Returns:
            Dataframe: Single thing's value stream data for selected properties
             with thingName, timestamp, and cell
        """
        thing_data = self.get_things.get_property_history(thingName=thing, propertyList=propertyList,
                                                          startDate=self.start_date, endDate=self.end_date,
                                                          maxItems=self.maxItems)  # 86400 rows per day per thing
        if len(thing_data) > 0:
            thing_data['cell'] = None
            thing_data['cell'] = cell
            thing_data['thingworx_name'] = thing
            thing_data['timestamp'] = pd.to_datetime(thing_data['timestamp'])
            thing_data['unix_timestamp'] = thing_data['timestamp'].astype(int) // 10 ** 9
            thing_data['id'] = (thing_data['unix_timestamp']).astype(str) + '_' + str(fac_no)
            thing_data = thing_data.drop(columns=['unix_timestamp'])
        else:
            thing_data = None

        return thing_data

    def get_all_thing(self, thingType: str = None) -> pd.DataFrame:
        """
        Get all things information from given Project name in config and select based on thing type
        Example of thing type: Thing, ThingShape, ThingTemplate, Mashup, DataShape
        Args:
            thingType: thing type of interest
        Returns:
            DataFrame: Thing name and thing type
        """
        all_things = self.get_things.get_project_things(self.project)
        print('Types of Things: ', all_things['type'].unique())

        if thingType is not None:
            print('Things Type: ', thingType)
            all_things = all_things[all_things['type'] == f'{thingType}'].copy()

        return all_things

    def get_thing_meta(self, templates: list = None) -> pd.DataFrame:
        """
        Get all things meta info from given templates
            thing name, cell, facility name, equipment type, thing template, facility model no,
             industrial thing, connection status
        Args:
            templates: list of thing templates
        Returns:
            DataFrame: Combined things metadata from list of templates
        """
        if templates is None:
            templates = list(self.templateName)
        thingInfo_comb = pd.DataFrame()
        print('Templates from config: ', templates)
        for template in templates:
            thingName = self.get_things.thing_name(template=template)
            print('thingName: ', thingName)
            for thing in thingName:
                thingInfo = self.get_things.thing_info(thingName=thing)
                thingInfo_comb = pd.concat([thingInfo_comb, thingInfo], ignore_index=True)

        print(thingInfo_comb)
        return thingInfo_comb

    def update_thing_info(self, data: pd.DataFrame, replace: bool = False):
        """
        Update or replace database table based on replace flag
        Args:
            data: new data in dataframe format
            replace: True to replace existing table, false to append to existing table
        Returns:
        """
        from sdm_tbl import thing_info

        sql_dict, map_dict, sql_query, tbl_name = thing_info(schema=self.schema, tblName=self.table_name)
        ret = inspect(self.eng).has_table(
            raw_tbl,
            schema=self.schema,
            )
        if ret:
            sql = 'SELECT * FROM {schema}.{tbl}'.format(schema=self.schema, tbl=tbl_name)
            exist_data = pd.read_sql_query(sql, con=self.eng)
            print('Read existing data:\n', exist_data)
            new_data = data.rename(columns=map_dict)
            new_data['updated_timestamp'] = self.now
            print('Read new data:\n', new_data)

            if replace:
                print('Replace Table')
                new_data.to_sql(f'{tbl_name}', con=self.eng, if_exists='replace', schema=self.schema,
                                index=False, dtype=sql_dict)
            else:
                print('Append Table')
                no_dup_df = new_data[~new_data['thingworx_name'].isin(exist_data['thingworx_name'])].copy()
                print('inside no_dup_df:\n', no_dup_df)
                no_dup_df.to_sql(f'{tbl_name}', con=self.eng, if_exists='append', schema=self.schema,
                                 index=False, dtype=sql_dict)
        else:
            print(f'{tbl_name} not found in {self.schema} schema')

    @staticmethod
    def column_fillna(df: pd.DataFrame, fil: list) -> pd.DataFrame:
        """
        Fill null with NaN for list of selected columns
        Args:
            df: list of thing templates
            fil: selected list of columns name
        Returns:
            DataFrame: return data with NaN imputation
        """
        for col in fil:
            if col not in df.columns:
                df[col] = np.nan
        return df

    def template_valid(self, template: str) -> list:
        """
        Check if given template name is available in ThingWorx
         and return all things from that template
        Args:
            template: template name
        Returns:
            list: all thing name under the given template
        """
        valid_template = self.get_all_thing(thingType='ThingTemplate')
        valid_template = valid_template['name'].unique().tolist()

        if template in valid_template:
            things = self.get_things.thing_name(template=template)
        else:
            print('Template not found')

        return things

    def load_mtr_vs(self, template: str, raw_tbl: str, prodOnly: bool = True):
        """
        Load thing value stream data from motor related templates into SDM database
        Args:
            template: template name
            raw_tbl: name of raw data table
            prodOnly: if True, load only production date from MES data
        Returns:
            Data insertion into SDM database
        """
        if template is None:
            template = self.templateName
            print('Templates from config: ', template)
        else:
            print('Templates from input: ', template)

        sql = "SELECT * FROM {schema}.{tbl} WHERE raw_data_tbl = '{tbl_name}'".format(schema=self.schema,
                                                                                      tbl='mtr_tbl_info',
                                                                                      tbl_name=raw_tbl)
        mtr_info = pd.read_sql_query(sql, con=self.eng)
        things = mtr_info['thingworx_name'].to_list()

        prop_list = str(config_param(config_file=self.twx_config,
                                     field=f'{template}')).replace(' ', '').split(',')

        if template == 'SEW_INVERTER_TEMPLATE':
            sql_dict, map_dict, _ = sew_mtr_raw(schema=self.schema, tblName=raw_tbl)

        if template == 'SIEMENS_SERVO_MOTOR_TEMPLATE':
            sql_dict, map_dict, _ = sie_mtr_raw(schema=self.schema, tblName=raw_tbl)

        if template == 'RIT_AIRCON_TEMPLATE':
            sql_dict, map_dict, _ = aircon_tbl(schema=self.schema, tblName=raw_tbl)

        ret = self.insp.dialect.has_table(self.eng.connect(), raw_tbl)

        if len(things) > 0:

            for thing in things:
                logger.info('Load data from thing: ' + str(thing))
                thing_info = self.sdm.get_thing_info(thing=thing)
                cell = thing_info['cell'].unique()[0]
                prod_date_list = self.get_things.get_prod_date(startDate=self.start_str, endDate=self.end_str,
                                                               cell=cell, prodOnly=prodOnly)

                for date in prod_date_list:
                    logger.info('Load from date: ' + str(date))
                    self.gen_date(startDate=date)
                    vs = self.get_thing_vs(propertyList=prop_list, thing=thing,
                                           cell=cell, fac_no=thing_info['facility_no'].values[0])
                    if vs is not None:
                        vs = vs.rename(columns=map_dict)
                        vs['updated_timestamp'] = self.now

                        if ret:
                            new_data = vs.copy()

                            if "id" not in new_data.columns:
                                raise ValueError(
                                    "Telemetry records require an id column"
                                )

                            if new_data["id"].isna().any():
                                raise ValueError(
                                    "Telemetry IDs cannot contain null values"
                                )

                            inserted = upsert_dataframe(
                                df=new_data,
                                engine=self.eng,
                                table_name=raw_tbl,
                                schema=self.schema,
                                conflict_columns=["id"],
                                batch_size=1000,
                                update_existing=False,
                            )

                            logger.info(
                                "Telemetry ingestion completed: "
                                "table=%s equipment=%s extracted=%d inserted=%d",
                                raw_tbl,
                                thing,
                                len(new_data),
                                inserted,
                            )
                        else:
                            logger.warning('Table not found in schema: ' + raw_tbl)
                            print(f'{raw_tbl} not found in {self.schema} schema')
                    else:
                        logger.warning('No property data on selected date: ' + date)
                        print('No property data on selected date')
        else:
            logger.critical('Thing not found in map/template:' + str(things))


if __name__ == '__main__':
    start_time = time.time()
    sdm = SDM_PIPELINE(schedule=False)
    # template_name = sdm.get_all_thing(thingType='ThingTemplate')
    # print(template_name)
    # thing_info_df = sdm.get_thing_meta(templates=['RIT_AIRCON_TEMPLATE'])
    # sdm.update_thing_info(data=thing_info_df, replace=False)
    # sdm.vs_data_extract(templates=['SEW_INVERTER_TEMPLATE'])
    raw_mtr_table = 'sie_mtr_raw_fc'
    sdm.load_mtr_vs(template='SIEMENS_SERVO_MOTOR_TEMPLATE', raw_tbl=raw_mtr_table , prodOnly=True)
    print("--- %s seconds ---" % (time.time() - start_time))
