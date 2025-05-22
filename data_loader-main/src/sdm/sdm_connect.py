# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from definitions import CONFIG_DIR

import pandas as pd

from src.utils.sdm_client import pg_client, pg_cursor
from src.utils.utilities import config_param
import numpy as np

from sqlalchemy import DateTime, Float, Integer, String, ARRAY


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 28)


class SDMConnect(object):
    def __init__(self, config_file: str = ''):
        self.config = config_file
        self.db_config = config_param(config_file=f'{CONFIG_DIR}/sdm_config.yaml', field='sdm_db')
        self.load_data = config_param(config_file=f'{CONFIG_DIR}/sdm_config.yaml', field='load_data')
        self.eng, self.conn, self.sess, self.insp = pg_client(config=self.db_config)
        self.schema = self.db_config['schema']
        self.table_name = self.load_data['table_name']

    def read_table(self, tbl_name: str) -> pd.DataFrame:

        """
        Read table data from database in form of pandas dataframe
        Args:
            tbl_name: Database table name
        Returns:
            DataFrame: Dataframe from selected table
        """

        sql = 'SELECT * FROM {schema}.{tblName}'.format(schema=self.schema, tblName=tbl_name)
        data = pd.read_sql_query(sql, con=self.conn)
        print(data)
        data.to_csv(tbl_name+'_output.csv', index = False)
        return data

    def read_db(self):
        print(f'Tables inside {self.schema} schema:', self.insp.get_table_names())

    def create_table(self, tbl_name: str, query: str):
        """
        Create table in database if not exist
        Args:
            tbl_name: Database table name
            query: Postgres SQL query for execution
        Returns:
        """
        ret = self.insp.dialect.has_table(self.eng.connect(), tbl_name)
        connection, cursor = pg_cursor()
        if ret:
            print(f'{tbl_name} Table found in {self.schema} schema')
        else:
            cursor.execute(query)
            connection.commit()
            cursor.close()
            print(f'create new tbl {tbl_name}')

    def update_table(self, data: pd.DataFrame, tbl_name: str, tbl_dict: dict, replace: bool = False):
        """
        Update or replace database table based on replace flag
        Args:
            data: new data in dataframe format
            tbl_name: Data table name in Postgres SQL
            tbl_dict: Dictionary of the data type
            replace: True to replace existing table, false to append to existing table
        Returns:
        """
        ret = self.insp.dialect.has_table(self.eng.connect(), tbl_name)

        if ret:
            sql = 'SELECT * FROM {schema}.{tbl}'.format(schema=self.schema, tbl=tbl_name)
            exist_data = pd.read_sql_query(sql, con=self.eng)
            print('Read existing data:\n', exist_data)
            new_data = data
            print('Read new data:\n', new_data)

            if replace:
                print('Replace Table')
                new_data.to_sql(f'{tbl_name}', con=self.eng, if_exists='replace', schema=self.schema,
                                index=False, dtype=tbl_dict)
            else:
                print('Append Table')
                no_dup_df = new_data[~new_data['thingworx_name'].isin(exist_data['thingworx_name'])].copy()
                print('inside no_dup_df:\n', no_dup_df)
                no_dup_df.to_sql(f'{tbl_name}', con=self.eng, if_exists='append', schema=self.schema,
                                 index=False, dtype=tbl_dict)
        else:
            print(f'{tbl_name} not found in {self.schema} schema')

    def get_fac_cls_tier(self) -> pd.DataFrame:

        """
        Read facility_clas_b and arrange index by class 3 code
        Args:
        Returns:
            DataFrame: fac_class from facility_clas_b
            with columns: class_3_no, class_3_cd, class_3_name,
            class_2_no, class_2_cd, class_2_name,
            class_1_no, class_1_cd, class_1_name
        """

        sql = ('SELECT a.facility_clas_no AS class_3_no, a.facility_clas_cd AS class_3_cd, '
               'a.facility_clas_name AS class_3_name, '
               'b.facility_clas_no AS class_2_no, b.facility_clas_cd AS class_2_cd,'
               'b.facility_clas_name AS class_2_name,'
               'c.facility_clas_no AS class_1_no, c.facility_clas_cd AS class_1_cd,'
               'c.facility_clas_name AS class_1_name '
               'FROM {schema}.{tbl} a JOIN {schema}.{tbl} b ON '
               'a.superior_facility_clas_no = b.facility_clas_no JOIN {schema}.{tbl} c ON '
               'b.superior_facility_clas_no = c.facility_clas_no '
               'WHERE a.facility_clas_no <> b.facility_clas_no '
               'AND b.facility_clas_no <> c.facility_clas_no'.format(schema=self.schema, tbl='facility_clas_b'))
        fac_class = pd.read_sql_query(sql, con=self.conn)
        print(fac_class)

        return fac_class

    def get_fac_cls_attr(self, classFilter: str = None) -> pd.DataFrame:

        """
        Read facility_clas_b and arrange index by class 3 code
        Args:
        Returns:
            DataFrame: JOIN facility_clas_b and facility_clas_collection_data_l
            with columns: facility_clas_cd, facility_clas_name, data_seqno, attribute_name, data_type
        """

        sql = ('SELECT fcb.facility_clas_cd, fcb.facility_clas_name, fcb.facility_clas_no, fccdl.data_seqno,'
               ' fccdl.attribute_name, fccdl.data_type '
               'FROM {schema}.{tbl1} fcb JOIN {schema}.{tbl2} fccdl '
               'ON fcb.facility_clas_no = fccdl.facility_clas_no '.format(schema=self.schema, tbl1='facility_clas_b',
                                                                          tbl2='facility_clas_collection_data_l'))
        fac_class = pd.read_sql_query(sql, con=self.conn)
        if classFilter is not None:
            fac_class = fac_class[fac_class['facility_clas_no'] == classFilter].copy()

        print(fac_class)

        return fac_class

    def get_fac_b_with_cls(self, kep_ch: str = None) -> pd.DataFrame:

        """
        Read facility no, name, clas_no, clas_cd, maker_cd and thingworx name from SDM
         using kepware channel name
        Args:
        Returns:
            DataFrame: JOIN facility_clas_b, facility_b and facility_tag_l
        """

        sql = ("SELECT DISTINCT ON (fb.facility_no) fb.*, fcb.facility_clas_cd, ftl.thingworx_industrial_connection "
               "FROM facility.facility_b fb "
               "INNER JOIN facility.facility_clas_b fcb ON fb.facility_clas_no = fcb.facility_clas_no "
               "INNER JOIN facility.facility_tag_l ftl ON fb.facility_no = ftl.facility_no "
               "WHERE fb.facility_no IN (SELECT facility_no FROM facility.facility_tag_l "
               "WHERE kepware_channel_name = '{ch}')").format(ch=kep_ch)

        fac_class = pd.read_sql_query(sql, con=self.conn)
        print(fac_class)

        return fac_class

    def get_thing_info(self, thing: str) -> pd.DataFrame:

        """
        Read thing_info table from database and filter by thing name
        Args:
            thing: Things Name
        Returns:
            DataFrame: Thing information
        """

        sql = ("SELECT * FROM {schema}.thing_info"
               " WHERE thingworx_name = '{thing}'").format(schema=self.schema, thing=thing)
        data = pd.read_sql_query(sql, con=self.conn)

        return data

    def get_fac_b_kepware(self, kep_ch: str = None) -> pd.DataFrame:

        sql = ("SELECT fcl.*, fccdl.attribute_name as standard_attribute_name, fccdl.data_type as standard_data_type "
               "FROM facility.facility_tag_l fcl "
               "INNER JOIN facility.facility_clas_collection_data_l fccdl "
               "ON fcl.facility_clas_no = fccdl.facility_clas_no and fcl.data_seqno = fccdl.data_seqno "
               "WHERE fcl.kepware_channel_name ='{ch}'").format(ch=kep_ch)

        kepware_tag = pd.read_sql_query(sql, con=self.conn)

        return kepware_tag

    def get_fac_b_maker(self, makerCd: str) -> dict:

        sql = ("SELECT * FROM facility.company "
               "WHERE maker_cd ='{cd}'").format(cd=makerCd)

        data = pd.read_sql_query(sql, con=self.conn)
        if data.empty:
            comp = {'company_name': np.nan, 'model_cd': np.nan, 'model_description': np.nan}
        else:
            comp = {'company_name': data['company_name'].values[0],
                    'model_cd': data['model_cd'].values[0],
                    'model_description': data['model_description'].values[0]}

        return comp

    def read_table_thg(self, tbl_name: str, thingName: str) -> pd.DataFrame:

        """
        Read table data from database in form of pandas dataframe
        Args:
            tbl_name: Database table name
            thingName: Thing's name
        Returns:
            DataFrame: Dataframe from selected table
        """
        sql = "SELECT * FROM {schema}.{tblName} WHERE thingworx_name LIKE '{thingName}' ".format(schema=self.schema,
                                                                                                 tblName=tbl_name,
                                                                                                 thingName=thingName)
        data = pd.read_sql_query(sql, con=self.conn)
        print(data)

        return data

    def create_tbl_template(self):
        
        from sdm_tbl import sie_mtr_raw, sew_mtr_raw, aircon_tbl
        sql_dict, mapDict, sql_query = aircon_tbl(schema='m13', tblName=self.table_name)
        self.create_table(tbl_name=self.table_name, query=sql_query)


################################################################################
#------------------------------------------------------------------------------#
################################################################################
if __name__ == '__main__':
    # --- Configuration ---
    db_config_file = f'{CONFIG_DIR}/sdm_config.yaml'
    excel_file_path = 'DB_TIMESERIES_DATA.xlsx'
    target_table_name = 'gbx_operating_hrs'

    # --- Instantiate Connector ---
    print(f"Initializing SDMConnect using config: {db_config_file}")
    try:
        conn = SDMConnect(config_file=db_config_file)
        print(f"Successfully connected. Operating on schema: '{conn.schema}'")
        if conn.schema != 'm13_dev':
            print(f"*** WARNING: Configured schema is '{conn.schema}', but expected 'm13_dev'. Verify config. ***")
            # exit() # Decide if you want to stop execution
    except Exception as e:
        print(f"Error initializing SDMConnect: {e}")
        print("Check database configuration ('sdm_config.yaml') and connectivity.")
        exit()

    # --- Read Data from Excel ---
    print(f"Reading data from '{excel_file_path}'...")
    try:
        df = pd.read_excel(excel_file_path)
        print(f"Successfully read {len(df)} rows from Excel.")
        print("Original Excel Data Head:")
        print(df.head())

        # --- Data Preparation ---
        print("Preparing data (converting types and checking ID uniqueness)...")

        # Check for duplicate IDs *before* attempting to load
        if df['id'].duplicated().any():
            print("*** ERROR: Duplicate IDs found in the Excel file! Cannot use ID as Primary Key. ***")
            print("Duplicate IDs:")
            print(df[df['id'].duplicated(keep=False)]['id'])
            exit() # Stop execution if duplicates are found
        else:
            print("Verified: All IDs in the Excel file are unique.")

        # Convert 'timestamp'
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            if df['timestamp'].isnull().any():
                 print("Warning: Some 'timestamp' values could not be parsed.")
        except Exception as e:
            print(f"Error converting 'timestamp' column: {e}. Check Excel format.")
            exit()

        # Convert other columns
        df['id'] = df['id'].astype(str)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        if df['value'].isnull().any():
            print("Warning: Some 'value' entries were non-numeric and converted to NaN.")
        df['thingworx_name'] = df['thingworx_name'].astype(str)
        df['property'] = df['property'].astype(str)

        print("DataFrame Info after type conversion:")
        df.info()
        print("Prepared Data Head:")
        print(df.head())

    except FileNotFoundError:
        print(f"Error: Excel file not found at '{excel_file_path}'")
        exit()
    except Exception as e:
        print(f"Error reading or processing Excel file: {e}")
        exit()

    # --- Define Table Structure ---
    # MODIFIED: Added PRIMARY KEY constraint to the 'id' column
    create_table_query = f"""
    CREATE TABLE {conn.schema}.{target_table_name} (
        id VARCHAR PRIMARY KEY,
        timestamp TIMESTAMPTZ,
        thingworx_name VARCHAR,
        property VARCHAR,
        value FLOAT4
    );
    """

    # Define SQLAlchemy types dictionary - no change needed here for PK
    sql_alchemy_dtypes = {
        'id': String,
        'timestamp': DateTime(timezone=True),
        'thingworx_name': String,
        'property': String,
        'value': Float
    }

    # --- Create Table ---
    # NOTE: If the table already exists *without* the primary key,
    # this `create_table` method (as provided) will *not* modify it.
    # You might need to manually DROP the old table first if its structure needs changing.
    print(f"\nAttempting to create table '{conn.schema}.{target_table_name}' with ID as PRIMARY KEY...")
    conn.create_table(tbl_name=target_table_name, query=create_table_query)

    # --- Push Data to Table ---
    # Added try-except to catch potential IntegrityError due to PK violation
    print(f"\nAttempting to load data into '{conn.schema}.{target_table_name}' (replacing existing data)...")
    try:
        conn.update_table(data=df,
                            tbl_name=target_table_name,
                            tbl_dict=sql_alchemy_dtypes,
                            replace=True) # replace=True should ideally handle pre-existing data cleanly
    except Exception as e:
        # Catching a general Exception, but IntegrityError is the most likely cause for PK issues
        print(f"*** ERROR loading data into table: {e} ***")
        print("*** This might be due to duplicate IDs if the initial check failed or if replace=False was used on existing data. ***")
        # You might want specific handling for different exception types (e.g., sqlalchemy.exc.IntegrityError)
        # import sqlalchemy
        # except sqlalchemy.exc.IntegrityError as ie:
        #    print(f"Database Integrity Error (likely duplicate primary key): {ie}")
        # except Exception as e:
        #    print(f"An unexpected error occurred during data loading: {e}")


    # --- Verification (Optional) ---
    print(f"\nVerification: Reading first few rows from '{conn.schema}.{target_table_name}'...")
    try:
        conn.read_table(target_table_name)
    except Exception as e:
        print(f"Could not read table for verification: {e}")

    print("\nScript finished.")



#if __name__ == '__main__':
#     db_config = f'{CONFIG_DIR}/sdm_config.yaml'
#     conn = SDMConnect(config_file=db_config)

# #READ TABLE
# tbl_name = 'prod_assembly_tbl_tx'
# conn.read_table(tbl_name)


#     # create_table_query = """
#     # CREATE TABLE m13_dev.sie_mtr_agg_data_cm3 (
#     #     id VARCHAR PRIMARY KEY,
#     #     timestamp TIMESTAMPTZ,
#     #     cell VARCHAR,
#     #     thingworx_name VARCHAR,
#     #     current FLOAT4,
#     #     temperature FLOAT4,
#     #     voltage_input FLOAT4,
#     #     position FLOAT4,
#     #     torque FLOAT4,
#     #     updated_timestamp TIMESTAMPTZ
#     # );
#     # """
#     # conn.create_table(tbl_name="sie_mtr_agg_data_cm3", query=create_table_query)


#     # data = pd.read_csv("filtered_with_margin.csv", dtype={
#     #     "id": str,  # Since id is VARCHAR
#     #     "cell": str,
#     #     "thingworx_name": str
#     # })

#     # # Convert timestamp columns
#     # data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
#     # data["updated_timestamp"] = pd.to_datetime(data["updated_timestamp"], utc=True)

#     # # Ensure float columns are correct
#     # float_cols = ["current", "temperature", "voltage_input", "position", "torque"]
#     # data[float_cols] = data[float_cols].astype(float)
#     # data = data.drop_duplicates(subset=['id'])

#     # tbl_dict = {
#     #     "id": String,  
#     #     "timestamp": DateTime(timezone=True),
#     #     "cell": String,
#     #     "thingworx_name": String,
#     #     "current": Float,
#     #     "temperature": Float,
#     #     "voltage_input": Float,
#     #     "position": Float,
#     #     "torque": Float,
#     #     "updated_timestamp": DateTime(timezone=True)
#     # }

#     # conn.update_table(
#     #     data=data,
#     #     tbl_name="sie_mtr_agg_data_cm3",
#     #     tbl_dict=tbl_dict,
#     #     replace=False  # False = Append, True = Replace
#     #     )



#     # kepwareTag = conn.get_fac_b_kepware(kep_ch='L8_CARLIFT_MCP')
#     # print(kepwareTag.head())
#     # cc = conn.get_fac_b_with_cls('L8_CARLIFT_MCP')
#     # df = conn.read_table_thg(tbl_name='siemens_mtr_tbl', thingName='FE4_SEALER_SERVO1')

