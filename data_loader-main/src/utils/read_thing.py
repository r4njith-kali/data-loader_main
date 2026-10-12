# Created by aaronkueh at 5/4/24

import pandas as pd
import numpy as np

from definitions import CONFIG_DIR
from src.utils.api_client import ApiClient
from src.utils.utilities import config_param
from datetime import datetime

pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 12)
pd.set_option('display.max_rows', 500)


class GetThings(object):
    def __init__(self, config_file: str = '', templateFromConfig: bool = True):
        self.config = config_file
        self.client = ApiClient(config_file=self.config)
        self.templateFromConfig = templateFromConfig
        self.tempType = str(config_param(config_file=self.config, field='template_type'))
        self.templateName = str(config_param(config_file=self.config,
                                             field='template_name')).replace(' ', '').split(',')
        self.excludeTemplate = str(config_param(config_file=self.config,
                                                field='exception_template')).replace(' ', '').split(',')
        self.now = datetime.now()
        self.sensorLive = int(config_param(config_file=self.config, field='sensorLive'))
        self.statusLive = int(config_param(config_file=self.config, field='statusLive'))
        asset_str = str(config_param(config_file=self.config, field='status_list')).replace(' ', '').split(',')
        self.status = list(map(str, asset_str))
        print('current time:', self.now)


    def thing_name(self, template: str = None) -> list:
        """Retrieve unique Thing names from configured templates.

        Args:
            template: Template to query when templateFromConfig is False.

        Returns:
            List of unique Thing names in discovery order.
        """
        if self.templateFromConfig:
            templates = self.templateName
        else:
            if not template:
                raise ValueError(
                    "A template name must be provided when "
                    "templateFromConfig is False"
                )
            templates = [template]

        things = []
        seen = set()

        for template_name in templates:
            if not template_name:
                continue

            endpoint = (
                f"ThingTemplates/{template_name}/ImplementingThings"
            )

            response = self.client.get_request(endpoint)

            if not isinstance(response, dict):
                raise ValueError(
                    f"Unexpected API response for {template_name}"
                )

            rows = response.get("rows")

            if not isinstance(rows, list):
                raise ValueError(
                    f"Missing or invalid rows for {template_name}"
                )

            for row in rows:
                if not isinstance(row, dict):
                    continue

                name = row.get("name")

                if name and name not in seen:
                    seen.add(name)
                    things.append(name)

        return things
    
        """
        Extract Thing name from given template.
            Read from config or read from user input
         Args:
            template (str): Template name from input
        Returns:
            list: all things name from given thing template
        """
        things_list = []
        if self.templateFromConfig:
            templates = list(self.templateName)
            for template in templates:
                print('Check template: ', template)
                ImplementingThings = self.client.get_request(f'ThingTemplates/{template}/ImplementingThings')
            print('Extract things templates from config:\n', templates)
        else:
            ImplementingThings = self.client.get_request(f'ThingTemplates/{template}/ImplementingThings')

        for i in range(len(ImplementingThings['rows'])):
            things_list.append(ImplementingThings['rows'][i]['name'])

        print('Number of things:', len(things_list))

        return things_list
    
    # Inside the GetThings class:

    # Inside the GetThings class:

    def get_all_thing_names(self, page_size: int = 500) -> list:
        """
        Retrieves a list of ALL Thing names from the ThingWorx instance,
        handling pagination.
        Args:
            page_size (int): How many items to request per API call.
                            Check ThingWorx docs/limits for optimal/max values.
        Returns:
            list: A list of all Thing names.
        """
        print(f"Attempting to retrieve all Thing names (page size: {page_size})...")
        all_thing_names = []
        offset = 0
        more_items = True

        while more_items:
            # Construct the API endpoint with pagination parameters
            # Common OData style: /Things?$top=500&$skip=0
            # Adjust '$top' and '$skip' if your ThingWorx uses different param names
            endpoint = f'Things?$top={page_size}&$skip={offset}'
            print(f"  Fetching: {endpoint}")

            try:
                response = self.client.get_request(endpoint)

                if 'rows' in response and isinstance(response['rows'], list):
                    current_page_things = [thing.get('name') for thing in response['rows'] if 'name' in thing]
                    count_on_page = len(current_page_things)

                    if count_on_page > 0:
                        all_thing_names.extend(current_page_things)
                        print(f"    Fetched {count_on_page} items. Total so far: {len(all_thing_names)}")
                        if count_on_page < page_size:
                            # If we received fewer items than requested, it must be the last page
                            print("    Reached last page (received fewer items than page size).")
                            more_items = False
                        else:
                            # Prepare for the next page
                            offset += page_size
                    else:
                        # No items returned on this page, we're done
                        print("    Reached last page (received 0 items).")
                        more_items = False
                else:
                    print(f"Error: Unexpected response format or missing 'rows' from {endpoint}. Stopping.")
                    # Log response details for debugging if needed
                    # print(f"Response keys: {response.keys()}")
                    # print(f"Response snippet: {str(response)[:500]}")
                    more_items = False # Stop pagination on error/unexpected format

            except Exception as e:
                # Catch potential errors from api_client or JSON parsing
                print(f"Error retrieving page at offset {offset}: {e}")
                more_items = False # Stop pagination on error

        print(f"Finished fetching. Found {len(all_thing_names)} total Things after pagination.")
        return all_thing_names

    def thing_value(self, thingName: str) -> pd.DataFrame():
        """
        Read value, timestamp and quality flag of given ThingName
        URL Example: http://10.107.108.136/Thingworx/Things/FC1_DMM11-SVM11/PropertiesVTQ/
        Args:
            thingName: thing name from Things
        Returns:
            dataframe: value, timestamp and quality flag of given ThingName
        """

        vtq = self.client.get_request(f'Things/{thingName}/PropertiesVTQ/')
        vtq3 = list(vtq['rows'][0].values())
        vtq3_list = []
        for i in range(len(vtq3)):
            vtq3_list.append(vtq3[i]['rows'])

        thing_vtq = pd.DataFrame({'propertyName': vtq['rows'][0].keys(),
                                  'propertyValue': vtq3_list})
        thing_vtq['propertyValue'] = pd.DataFrame(thing_vtq['propertyValue'].values.tolist(), index=thing_vtq.index)
        thing_vtq = thing_vtq.join(pd.DataFrame(thing_vtq.pop('propertyValue').values.tolist()))

        # Convert 13-digit unix time in ms to timestamp
        thing_vtq['time'] = pd.to_datetime((thing_vtq['time'] / 1000), unit='s', utc=True, dayfirst=True)
        thing_vtq['time'] = (thing_vtq['time'].dt.tz_convert(tz='Asia/Singapore')).dt.strftime("%Y-%m-%d %H:%M:%S")
        thing_vtq = thing_vtq.rename(columns={'value': 'propertyValue', 'time': 'propertyTime',
                                              'quality': 'propertyQuality'})

        return thing_vtq

    # noinspection PyBroadException
    def thing_tag(self, thingName: str, thgProperties: list) -> pd.DataFrame():
        """
        Read thing name and property name to retrieve kepware tag address
        Args:
            thingName: thing name from Things
            thgProperties: list of properties name from Things
        Returns:
            dataframe: dictionary of property name, and it's kepware tag address
        """
        thingName = thingName
        api_input = dict()
        kepware_list, property_list, type_list = [], [], []

        for thgProperty in thgProperties:
            api_input['propertyName'] = thgProperty
            try:
                binding = self.client.post_request(api=f'Things/{thingName}/Services/GetRemotePropertyBinding/',
                                                   parameters=api_input)
                kepwareTag = binding['rows'][0]['aspects']['tagAddress']
                industrialDataType = binding['rows'][0]['aspects']['industrialDataType']
                kepware_list.append(kepwareTag)
                property_list.append(thgProperty)
                type_list.append(industrialDataType)
            except:
                pass

        tag_dict = pd.DataFrame({'propertyName': property_list,
                                 'industrialDataType': type_list, 'tagAddress': kepware_list})

        return tag_dict

    def quality_live(self, thingName: str) -> [pd.DataFrame(), bool, str]:
        """
        summarize thing with vtq, kepware tag and isLive status based on delta hour defined in config
        Args:
            thingName: thing name from Things
        Returns:
            dataframe: dictionary of vtq, kepware tag and isLive status
            bool: all tag isLive True
            str: all tag quality Good
        """

        stat = '|'.join(self.status)
        thing_vtq = self.thing_value(thingName=thingName)
        prop_list = thing_vtq['propertyName']
        tag_list = self.thing_tag(thingName=thingName, thgProperties=prop_list)
        vtq_tag = thing_vtq.merge(tag_list, how='left', on='propertyName')
        vtq_tag = (vtq_tag[vtq_tag['propertyName'] != 'name'].copy()).reset_index(drop=True)
        vtq_tag = vtq_tag.dropna(subset=['tagAddress']).reset_index(drop=True)
        vtq_tag['thingName'] = thingName

        # Defining sensor/status Live status based on delta hour
        vtq_tag['propertyTime'] = pd.to_datetime(vtq_tag['propertyTime'])
        vtq_tag['deltaHour'] = round(((self.now - vtq_tag['propertyTime']).dt.total_seconds()) / 3600, 1)
        sensorCond = (vtq_tag['industrialDataType'] == 'NUMBER') & (vtq_tag['deltaHour'] <= self.sensorLive)
        statusCond = (((vtq_tag['industrialDataType'] == 'BOOLEAN') |
                       (vtq_tag['industrialDataType'] == 'INTEGER') |
                       (vtq_tag['propertyName'].str.contains(stat)))
                      & (vtq_tag['deltaHour'] <= self.statusLive))

        vtq_tag['isLive'] = np.where(sensorCond, True, np.where(statusCond, True, False))
        col_name = ['thingName', 'propertyName', 'propertyValue', 'propertyTime', 'propertyQuality',
                    'industrialDataType', 'tagAddress', 'deltaHour', 'isLive']
        vtq_tag = vtq_tag.reindex(columns=col_name)
        allLive = bool([True if len(vtq_tag[vtq_tag['isLive'] == False]) == 0 else False][0])
        allGood = ['BAD' if len(vtq_tag[vtq_tag['propertyQuality'] == 'BAD']) > 0 else 'GOOD'][0]

        return vtq_tag, allLive, allGood

    def thing_info(self, thingName: str) -> pd.DataFrame():
        """
        Read value, timestamp and quality flag of given ThingName
        URL Example: http://10.107.108.136/Thingworx/Things/FC1_DMM11-SVM11/Properties/
        Args:
            thingName: thing name from Things
        Returns:
            dataframe: thing facility info data
        """
        infoProperty = ['thingName', 'CELL', 'FACILITY_NAME', 'EQUIPMENT_TYPE', 'thingTemplate',
                        'FACILITY_MODEL_NO', 'IndustrialThing', 'isConnected']
        thingInfo = self.client.get_request(f'Things/{thingName}/Properties/')
        thingInfo = thingInfo['rows'][0]
        infoDict = pd.DataFrame(data=[thingInfo.values()], columns=thingInfo.keys())
        infoDict = infoDict.rename(columns={'name': 'thingName'})

        try:
            infoDict = infoDict[infoProperty]
        except KeyError:
            print('Failed Thing', thingName)

        return infoDict

    def thing_qc(self) -> pd.DataFrame():
        """
        Compile isLive, isConnected and quality flag at Thing level for all Things from given template
        based on overall properties check
        Args:
        Returns:
            dataframe: Thing facility info data with isLive, and quality flag
        """
        things = self.thing_name()
        qcTable = pd.DataFrame()
        for thing in things:
            print('Load thing:', thing)
            _, liveFlg, goodFlg = self.quality_live(thingName=thing)
            thgInfo = self.thing_info(thingName=thing)
            thgInfo['isLive'] = liveFlg
            thgInfo['quality'] = goodFlg
            qcTable = pd.concat([qcTable, thgInfo])

        qcTable.reset_index(drop=True, inplace=True)
        return qcTable

    def tag_qc(self):
        """
        Compile kepware tag address, delta hour and isLive at properties level
        for all Things from given template
        Args:
        Returns:
            dataframe: Things properties data with tag address, delta hour and isLive flag
        """
        things = self.thing_name()
        tagTable = pd.DataFrame()
        for thing in things:
            print('Load thing:', thing)
            tag_ql, _, _ = self.quality_live(thingName=thing)
            tagTable = pd.concat([tagTable, tag_ql])

        tagTable.reset_index(drop=True, inplace=True)
        return tagTable

    def thing_tag_qc(self) -> [pd.DataFrame(), pd.DataFrame()]:
        """
        Compile isLive, isConnected and quality flag at Thing level for all Things from given template
        based on overall properties check
        Args:
        Returns:
            dataframe: Thing facility info data with isLive, and quality flagg
            dataframe: Things properties data with tag address, delta hour and isLive flag
        """
        things = self.thing_name()
        thingTable = pd.DataFrame()
        tagTable = pd.DataFrame()
        for thing in things:
            print('Load thing:', thing)
            tag_ql, liveFlg, goodFlg = self.quality_live(thingName=thing)
            tagTable = pd.concat([tagTable, tag_ql])
            thgInfo = self.thing_info(thingName=thing)
            thgInfo['isLive'] = liveFlg
            thgInfo['quality'] = goodFlg
            thingTable = pd.concat([thingTable, thgInfo])

        tagTable.reset_index(drop=True, inplace=True)
        thingTable.reset_index(drop=True, inplace=True)
        return thingTable, tagTable

    def prop_hist(self, thingName: str, startDate: str, endDate: str, asc: bool = False) -> pd.DataFrame():
        """
        Query Thing's properties history based on Thing name, start date and end date
        Args:
            thingName: Thing name
            startDate: Start Date in format YYYY-MM-DD
            endDate: End Date in format YYYY-MM-DD
            asc: sort ascending or descending
        Returns:
            dataframe: Properties historical data for given thingName
        """

        # Define QueryPropertyHistory API input parameters
        req_body = dict()
        req_body['oldestFirst'] = asc
        req_body['maxItems'] = 500
        req_body['endDate'] = endDate
        req_body['startDate'] = startDate
        req_body['fillOption'] = None
        post_req = self.client.post_request(api=f'Things/{thingName}/Services/QueryPropertyHistory/',
                                            parameters=req_body)
        hist_df = pd.DataFrame.from_dict(data=post_req['rows'])
        if len(hist_df) > 1:
            print(hist_df)
            hist_df['unix_timestamp'] = hist_df['timestamp']
            hist_df['timestamp'] = pd.to_datetime((hist_df['timestamp']), origin='unix', unit='ms',
                                                  utc=True, dayfirst=True)
            hist_df['timestamp'] = (hist_df['timestamp'].dt.tz_convert(tz='Asia/Singapore')).dt.strftime(
                "%Y-%m-%d %H:%M:%S.%f")
        else:
            print('No data')
            pass
        return hist_df

    def template_list(self) -> list:
        """
        Read all SDM template from Thingworx
        Args:
        Returns:
            list: PRDEQ and PMEQ template list
        """
        temp_list = []
        filter_list = tuple(['PRDEQ', 'PMEQ'])
        read_template = self.client.get_request(f'ThingTemplates/')
        for i in range(len(read_template['rows'])):
            temp_list.append(read_template['rows'][i]['name'])

        temp = [temp for temp in temp_list if temp.startswith(filter_list)]
        print('Number of templates found: ', len(temp))

        return temp

    def get_pm_orders(self):

        api_input = dict()
        api_input['start_date'] = '20240701'
        api_input['end_date'] = None

        sap_output = self.client.post_request(f'Things/Comm_SAP_M08/Services/M08_Get_PM_Orders',
                                              parameters=api_input)
        print(sap_output.keys())
        print(sap_output.values())
        for row in range(len(sap_output['rows'])):
            if (sap_output['rows'][row]['Activity_Type'] == 102) | (sap_output['rows'][row]['Activity_Type'] == 200):
                print(sap_output['rows'][row])

        return sap_output

    def get_project_things(self, projectName: str) -> pd.DataFrame:
        """
        Extract all entities for given Project name
        Args:
            projectName: Project name
        Returns:
            entities_df: entities df contains, thing, shape, template and all types of entities
        """

        things = self.client.post_request(f'Projects/{projectName}/Services/GetEntities')
        entities_df = pd.DataFrame(things['rows'])
        entities_df = entities_df.sort_values(by=['type']).reset_index(drop=True)
        print(entities_df)

        return entities_df

    def num_prop_hist(self, thingName: str, propertyName: str, maxItems: int,
                      startDate: str, endDate: str, asc: bool = False) -> pd.DataFrame():
        """
        Query Thing's number type properties history based on Thing name property name, start date and end date
        Args:
            thingName: Thing name
            propertyName: Thing number type property name
            maxItems: maximum number of items to query
            startDate: Start Date in format YYYY-MM-DDTHH:MM:SS.000Z
            endDate: End Date in format YYYY-MM-DDTHH:MM:SS.000Z
            asc: sort ascending or descending
        Returns:
            dataframe: Properties historical data for given thingName
        """

        # Define QueryPropertyHistory API input parameters
        req_body = dict()
        req_body['oldestFirst'] = asc
        req_body['maxItems'] = maxItems
        req_body['endDate'] = endDate
        req_body['startDate'] = startDate
        req_body['propertyName'] = propertyName
        post_req = self.client.post_request(api=f'Things/{thingName}/Services/QueryNumberPropertyHistory/',
                                            parameters=req_body)
        hist_df = pd.DataFrame.from_dict(data=post_req['rows'])
        if len(hist_df) > 0:
            hist_df['timestamp'] = pd.to_datetime((hist_df['timestamp']/1000), unit='s', utc=True, dayfirst=True)
            hist_df['timestamp'] = (hist_df['timestamp'].dt.tz_convert(tz='Asia/Singapore')).dt.strftime(
                "%Y-%m-%d %H:%M:%S")

        else:
            print(f'Property: {propertyName} has no data')
            pass

        return hist_df

    def get_property_history(self, thingName: str, propertyList: list,
                             startDate: str, endDate: str, maxItems: int) -> pd.DataFrame():
        """
        Querying each logged number type property on a Thing
         and then combining the individual datasets into one big data set
        Args:
            thingName: Thing name
            propertyList: List of multiple number type properties
            startDate: Start Date in format YYYY-MM-DDTHH:MM:SS.000Z
            endDate: End Date in format YYYY-MM-DDTHH:MM:SS.000Z
            maxItems: maximum number of items to query

        Returns:
            dataframe: Properties historical data for given thingName
        """

        comb_df = pd.DataFrame(columns=['timestamp'])
        for propertyName in propertyList:
            prop_df = self.num_prop_hist(thingName=thingName, propertyName=propertyName, maxItems=maxItems,
                                         startDate=startDate, endDate=endDate)
            if not prop_df.empty:
                prop_df = prop_df[['timestamp', 'value']].copy()
                prop_df = prop_df.rename(columns={'value': f'{propertyName}'})
                comb_df = comb_df.merge(prop_df, how='outer', on='timestamp')

        return comb_df.sort_values(by='timestamp', ascending=False)

    def get_prod_date(self, startDate: str, endDate: str, cell: str, prodOnly: bool = True) -> list:
        """
        Get Production earliest in and latest out datetime according to cell
        Args:
            startDate: Start Date in format YYYY-MM-DD
            endDate: End Date in format YYYY-MM-DD
            prodOnly: if True only return list of date according to input start and end date
            cell: Cell ID
        Returns:
            date_list: list of sorted production date
            date_list: if prodOnly is false, list of sorted date from input
        """

        if prodOnly:
            req_body = dict()
            req_body['startDate'] = startDate
            req_body['endDate'] = endDate
            post_req = self.client.post_request(api=f'Things/Comm_DSS_M13/Services/prodHour_MES/', parameters=req_body)
            prod_df = pd.DataFrame.from_dict(data=post_req['rows'])
            prod_df['CELL'] = prod_df['CELL'].astype(str).str.strip()
            date_list = (prod_df[prod_df['CELL'] == f'{cell}']['PROD_DATE']).to_list()
            print('Cell production date list', date_list)
        else:
            start_date = pd.to_datetime(startDate, format='%Y%m%d')
            end_date = pd.to_datetime(endDate, format='%Y%m%d')
            date_range = pd.date_range(start=start_date, end=end_date)
            date_list = date_range.strftime('%Y%m%d').tolist()
            print('Selected date list', date_list)

        return date_list

    def get_sap_equip(self) -> pd.DataFrame:
        """
        Get SAP equipment information through Comm_SAP_M13 services
        Args:
        Returns:
            sap_df: Dataframe of SAP equipment information (SAP equipment no.,
             equipment description, functional location and maker.
        """
        api_input = dict()
        api_input['input_param'] = '*'

        sap_output = self.client.post_request(f'Things/Comm_SAP_M13/Services/getEquipment',
                                              parameters=api_input)
        sap_df = pd.DataFrame.from_dict(data=sap_output['rows'])

        return sap_df
    
    # Inside the GetThings class:

    def get_things_from_template_list(self, template_list: list) -> list:
        """
        Extracts Thing names implementing any template from the provided list.

        Args:
            template_list (list): A list of Thing Template names.

        Returns:
            list: A list of unique Thing names implementing those templates.
        """
        all_things_list = []
        print(f"Getting implementing things for {len(template_list)} specific templates...")

        for template in template_list:
            print(f'  Checking template: {template}')
            try:
                # API endpoint to get things implementing a specific template
                endpoint = f'ThingTemplates/{template}/ImplementingThings'
                response = self.client.get_request(endpoint)

                # Check the response structure (usually {'rows': [{'name': 'Thing1'}, ...]})
                if 'rows' in response and isinstance(response['rows'], list):
                    implementing_things = [thing.get('name') for thing in response['rows'] if 'name' in thing]
                    count = len(implementing_things)
                    if count > 0:
                        print(f'    Found {count} implementing things.')
                        all_things_list.extend(implementing_things)
                    else:
                        print(f'    Found 0 implementing things.')
                else:
                    print(f"    Warning: Unexpected response format or no 'rows' for template {template}.")
                    # Optional: Log the response for debugging
                    # print(f"    Response snippet: {str(response)[:200]}")

            except Exception as e:
                # Catch potential errors from the API client or parsing issues
                print(f"    Error fetching things for template '{template}': {e}")
                # Decide if you want to continue with other templates or stop

        # Remove duplicates in case a Thing implements multiple templates in the list
        unique_things = sorted(list(set(all_things_list)))
        print(f"\nFound {len(unique_things)} unique things across the specified templates.")
        return unique_things

    # You can keep your original thing_name method as it was, or modify it
    # if you prefer a single method with more complex logic.
    # Adding a new method like above is often cleaner.


if __name__ == '__main__':
    import time
    start_time = time.time()
    config = f'{CONFIG_DIR}/api_config.yaml'

    # Initialize GetThings. templateFromConfig setting doesn't matter
    # for the new method we are calling.
    get_things_client = GetThings(config_file=config)

    # Define the list of templates you care about
    target_templates = [
    #    'KUKA_IIWA_JOINT_TEMPLATE',
    #    'KUKA_IIWA_CONTROLLER_TEMPLATE',
    #    'MAIN_MACHINE_TEMPLATE',
    #    'KUKA_IIWA_TEMPLATE',
    #    'PRDEQ_010112_TT',
    #    'DOOSAN_M1509_JOINT_TEMPLATE',
    #    'DOOSAN_M0617_JOINT_TEMPLATE',
    #    'DOOSAN_M1013_JOINT_TEMPLATE',
    #    'DOOSAN_H2017_JOINT_TEMPLATE'

        'UR_UR10_JOINT_TEMPLATE',
        'MAIN_MACHINE_TEMPLATE'
    ]

    print("\nFetching Things based on specific template list...")
    # Call the method to get things from templates
    relevant_things = get_things_client.get_things_from_template_list(target_templates)

    print(f"\nObtained {len(relevant_things)} things from templates. Now filtering for 'DOOSAN' or 'KUKA'...")

    # ---- ADD THIS FILTERING STEP ----
    # Use a list comprehension to filter the relevant_things list
    # Check if 'doosan' (lowercase) or 'kuka' (lowercase) is in the thing name (converted to lowercase)
    final_filtered_things = [
        name for name in relevant_things
        if 'ur_' in name.lower() #or 'kuka' in name.lower()
    ]
    # ---------------------------------

    print(f"\nFound {len(final_filtered_things)} things matching 'DOOSAN' or 'KUKA':")
    if final_filtered_things:
        # Print the final filtered list nicely
        for i in final_filtered_things:
            print(i)
    else:
        print("  No things containing 'DOOSAN' or 'KUKA' found in the initial list.")

    # You can now proceed to use the 'final_filtered_things' list
    # for further processing if needed

    end_time = time.time()
    print(f"\nScript finished in {end_time - start_time:.2f} seconds.")