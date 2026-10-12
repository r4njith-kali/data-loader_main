
import sqlalchemy as sal


def thing_qc_sum(schema) -> [dict, str, str]:
    tblName = 'thing_qc_sum'
    typeDict = {'qc_desc': sal.types.VARCHAR(length=255), 'num_things': sal.types.BigInteger(),
                'percent_things': sal.types.FLOAT()}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    qc_desc varchar(255), 
                    num_things integer,
                    percent_things real)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, sqlQuery, tblName


def thing_qc_tbl(schema) -> [dict, dict, str, str]:
    tblName = 'thing_qc'
    typeDict = {'thing_name': sal.types.VARCHAR(length=255), 'cell': sal.types.VARCHAR(length=255),
                'facility_name': sal.types.VARCHAR(length=255), 'equipment_type': sal.types.VARCHAR(length=255),
                'thing_template': sal.types.VARCHAR(length=255), 'facility_model_no': sal.types.VARCHAR(length=255),
                'industrial_thing': sal.types.VARCHAR(length=255), 'is_connected': sal.types.BOOLEAN,
                'is_live': sal.types.BOOLEAN, 'quality': sal.types.VARCHAR(length=255)}

    mapDict = {'thingName': 'thing_name', 'CELL': 'cell', 'FACILITY_NAME': 'facility_name',
               'EQUIPMENT_TYPE': 'equipment_type', 'thingTemplate': 'thing_template',
               'FACILITY_MODEL_NO': 'facility_model_no', 'IndustrialThing': 'industrial_thing',
               'isConnected': 'is_connected', 'isLive': 'is_live', 'quality': 'quality'}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    thing_name varchar(255), 
                    cell varchar(255),
                    facility_name varchar(255), 
                    equipment_type varchar(255), 
                    thing_template varchar(255), 
                    facility_model_no varchar(255), 
                    industrial_thing varchar(255), 
                    is_connected bool,
                    is_live bool, 
                    quality varchar(255))
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery, tblName


def m134_mtbf_tbl(schema) -> [dict, dict, str, str]:
    tblName = 'oee_mtbf'

    typeDict = {'id': sal.types.BIGINT, 'thingworx_name': sal.types.VARCHAR(),
                'facility_no': sal.types.VARCHAR(), 'breakdown_timestamp': sal.types.TIMESTAMP(timezone=True),
                'recovery_timestamp': sal.types.TIMESTAMP(timezone=True), 'comment': sal.types.VARCHAR()}

    mapDict = {'id': 'id', 'thingworx_name': 'thingworx_name', 'facility_no': 'facility_no',
               'breakdown_timestamp': 'breakdown_timestamp', 'recovery_timestamp': 'recovery_timestamp',
               'comment': 'comment'}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    id serial, 
                    thingworx_name varchar,
                    facility_no varchar, 
                    breakdown_timestamp pg_catalog.timestamptz, 
                    recovery_timestamp pg_catalog.timestamptz, 
                    comment varchar)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery, tblName


def thing_info(schema: str, tblName: str) -> [dict, dict, str]:

    typeDict = {'thingName': sal.types.VARCHAR(), 'CELL': sal.types.VARCHAR(), 'facility_no': sal.types.VARCHAR(),
                'FACILITY_NAME': sal.types.VARCHAR(), 'EQUIPMENT_TYPE': sal.types.VARCHAR(),
                'thingTemplate': sal.types.VARCHAR(), 'FACILITY_MODEL_NO': sal.types.VARCHAR(),
                'IndustrialThing': sal.types.VARCHAR(), 'update_timestamp': sal.types.TIMESTAMP(timezone=True)}

    mapDict = {'thingName': 'thingworx_name', 'CELL': 'cell', 'FACILITY_NAME': 'facility_name',
               'EQUIPMENT_TYPE': 'equipment_type', 'thingTemplate': 'thing_template',
               'FACILITY_MODEL_NO': 'facility_model_no', 'IndustrialThing': 'industrial_thing'}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    facility_no varchar,
                    thingworx_name varchar, 
                    facility_name varchar,
                    cell varchar, 
                    equipment_type varchar, 
                    thing_template varchar, 
                    facility_model_no varchar,
                    industrial_thing varchar, 
                    update_timestamp pg_catalog.timestamptz)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery

def aircon_tbl(schema: str, tblName: str) -> [dict, dict, str]:
    typeDict = {'timestamp': sal.types.TIMESTAMP(timezone=True),
                'cell': sal.types.VARCHAR(),
                'id': sal.types.VARCHAR(),
                'thingworx_name': sal.types.VARCHAR(),
                'INT_TEMP_VALUE': sal.types.VARCHAR(),
                'updated_timestamp': sal.types.TIMESTAMP(timezone=True)}

    mapDict = {'INT_TEMP_VALUE': 'temperature_int'}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    id varchar,
                    timestamp pg_catalog.timestamptz,
                    cell varchar,
                    thingworx_name varchar,
                    temperature_int real, 
                    updated_timestamp pg_catalog.timestamptz)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery

def sew_mtr_raw(schema, tblName) -> [dict, dict, str]:

    typeDict = {'timestamp': sal.types.TIMESTAMP(timezone=True), 'cell': sal.types.VARCHAR(), 'id': sal.types.VARCHAR(),
                'thingworx_name': sal.types.VARCHAR(), 'gap_value': sal.types.REAL(),
                'pow_unit_temp': sal.types.REAL(), 'cu_temp': sal.types.REAL(),
                'output_v': sal.types.REAL(), 'speed': sal.types.REAL(), 'torque': sal.types.REAL(),
                'updated_timestamp': sal.types.TIMESTAMP(timezone=True)}

    mapDict = {'CURRENT': 'current', 'GAPVALUE': 'gap_value', 'POW_UNIT_TEMP': 'pow_unit_temp',
               'CU_TEMP': 'cu_temp', 'OUTPUT_V': 'output_v', 'SPEED': 'speed', 'TORQUE': 'torque'}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    id varchar,
                    timestamp pg_catalog.timestamptz,
                    cell varchar,
                    thingworx_name varchar,
                    current real, 
                    gap_value real, 
                    pow_unit_temp real, 
                    cu_temp real, 
                    output_v real,
                    speed real,
                    torque real,
                    updated_timestamp pg_catalog.timestamptz)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery

def sie_mtr_raw(schema: str, tblName: str) -> [dict, dict, str]:

    typeDict = {'timestamp': sal.types.TIMESTAMP(timezone=True), 'cell': sal.types.VARCHAR(),
                'id': sal.types.VARCHAR(),
                'thingworx_name': sal.types.VARCHAR(), 'torque': sal.types.VARCHAR(),
                'temperature': sal.types.REAL(), 'current_input': sal.types.REAL(),
                'voltage_input': sal.types.REAL(), 'position': sal.types.REAL(),
                'STATUS_RUN': sal.types.INTEGER(),
                'updated_timestamp': sal.types.TIMESTAMP(timezone=True)}

    mapDict = {'TORQUE': 'torque', 'MOTOR_TEMP': 'temperature', 'CURRENT': 'current_input',
               'OUTPUT_V': 'voltage_input', 'POSITION': 'position', 'STATUS_RUN': 'status_run'}

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    id varchar,
                    timestamp pg_catalog.timestamptz,
                    cell varchar,
                    thingworx_name varchar,
                    current_input real, 
                    temperature real, 
                    voltage_input real,
                    position real,
                    torque real,
                    status_run int,
                    updated_timestamp pg_catalog.timestamptz)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery


def mtr_tbl_info(schema: str, tblName: str) -> [dict, dict, str]:

    typeDict = {'facility_no': sal.types.VARCHAR(),
                'raw_data_tbl': sal.types.VARCHAR(),
                'agg_data_tbl': sal.types.VARCHAR(),
                'vib_data_tbl': sal.types.VARCHAR(),
                'mtr_score_tbl': sal.types.VARCHAR(),
                'updated_timestamp': sal.types.TIMESTAMP(timezone=True)}

    mapDict = dict()

    sqlQuery = ''' 
                    CREATE TABLE {schema}.{tblName} (
                    facility_no varchar,
                    raw_data_tbl varchar,
                    agg_data_tbl varchar,
                    vib_data_tbl varchar,
                    mtr_score_tbl varchar,
                    updated_timestamp pg_catalog.timestamptz)
                 '''.format(schema=schema, tblName=tblName)

    return typeDict, mapDict, sqlQuery
