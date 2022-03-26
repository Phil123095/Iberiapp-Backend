import pandas as pd
import datetime
import os
import io


class FileHandler:
    def __init__(self, codes, filepath=None, s3_handler=None, s3_bucket=None):
        self.s3_handler = s3_handler
        self.bucket_name = s3_bucket
        self.__SHEETNAMES = ['MONTHLY INCIDENTS CLOSED', 'MONTHLY INCIDENTS BACKLOG', 'MONTHLY INCIDENTS RAISED']
        self.__COLNAMES = ['incident_code', 'customer_company_group', 'customer_company', 'creation_tstamp',
                           'resolution_tstamp', 'incident_status', 'incident_description', 'support_group',
                           'tower_group',
                           'domain_group', 'priority', 'resolution_description', 'assigned_organization',
                           'inc_category',
                           'last_mod_date', 'inc_type', 'inc_element', 'aging_days', 'client_loc', 'client_dept']

        self.__RAISEDCOLS = ['incident_code', 'customer_company_group', 'customer_company', 'creation_tstamp',
                             'resolution_tstamp', 'incident_status', 'incident_description', 'support_group',
                             'tower_group',
                             'domain_group', 'priority', 'urgency', 'resolution_description', 'assigned_organization',
                             'inc_category', 'last_mod_date', 'inc_type', 'inc_element', 'aging_days', 'client_loc',
                             'client_dept']

        self.__SLA_THRESHOLDS = {
            "Crítica": 4,
            "Alta": 8,
            "Media": 120,
            "Baja": 360
        }

        self.__CODES_TO_DEPT = codes

        if self.s3_handler:
            self.closed_incidents, self.backlog_incidents, self.raised_incidents = self.verify_and_load_file_S3()

        elif not self.s3_handler:
            self.closed_incidents, self.backlog_incidents, self.raised_incidents = self.verify_and_load_file_LOCAL(filepath)

        self.full_table = None
        self.frames = [self.closed_incidents, self.backlog_incidents]

        self.raised_summary = None
        self.all_incidents_summary = None

    def verify_and_load_file_S3(self):
        get_last_modified = lambda obj: int(obj['LastModified'].strftime('%s'))

        objs = self.s3_handler.list_objects_v2(Bucket='iberiapp-files')['Contents']
        last_added = [obj['Key'] for obj in sorted(objs, key=get_last_modified, reverse=True)][0]

        if '.xlsx' in last_added:
            #try:
            closed = self.get_correct_table(filepath=last_added, sheetname='MONTHLY INCIDENTS CLOSED', local=False)
            backlog = self.get_correct_table(filepath=last_added, sheetname= 'MONTHLY INCIDENTS BACKLOG', local=False)
            raised = self.get_correct_table(filepath=last_added, sheetname='MONTHLY INCIDENTS RAISED', local=False)

            return closed, backlog, raised
            #except ValueError:
            #    raise "Missing sheets."
        else:
            raise "File should be in xls format."

    def verify_and_load_file_LOCAL(self, filepath):
        if os.path.exists(filepath):
            if os.stat(filepath).st_size == 0:
                raise "File exists but is empty."
            else:
                if '.xlsx' in filepath:
                    if len(pd.ExcelFile(filepath).sheet_names) == 3:
                        closed = self.get_correct_table(filepath, 'MONTHLY INCIDENTS CLOSED', local=True)
                        backlog = self.get_correct_table(filepath, 'MONTHLY INCIDENTS BACKLOG', local=True)
                        raised = self.get_correct_table(filepath, 'MONTHLY INCIDENTS RAISED', local=True)

                        return closed, backlog, raised
                    else:
                        raise "Missing sheets."
                else:
                    raise "File should be in xls format."
        else:
            raise "File does not exist"


    def get_correct_table(self, filepath, sheetname, local=True):
        if local:
            in_df = pd.read_excel(filepath, sheet_name=sheetname)
        else:
            fileobject = self.s3_handler.get_object(Bucket='iberiapp-files', Key=filepath)
            in_df = pd.read_excel(io.BytesIO(fileobject['Body'].read()), sheet_name=sheetname)

        count = in_df.iloc[:, 3].first_valid_index()
        print(count)
        headers = in_df.iloc[count]
        new_df = pd.DataFrame(in_df.values[count + 1:], columns=headers)
        return new_df

    def clean_files(self):
        self.closed_incidents.columns = self.__COLNAMES
        self.backlog_incidents.columns = self.__COLNAMES
        self.raised_incidents.columns = self.__RAISEDCOLS

        self.closed_incidents['backlog_indicator'] = 'closed'
        self.backlog_incidents['backlog_indicator'] = 'backlog'

        self.full_table = pd.concat(self.frames)

        self.full_table = self.convert_dates(self.full_table, ['creation_tstamp', 'resolution_tstamp'])
        self.raised_incidents = self.convert_dates(self.raised_incidents, ['creation_tstamp', 'resolution_tstamp'])

        self.raised_summary = self.summarise_raised(self.raised_incidents)
        self.all_incidents_summary = self.summarise_incidents(self.full_table)

        self.all_incidents_summary['clean_date'] = self.all_incidents_summary['clean_date'].apply(
            lambda x: datetime.date.strftime(x, "%Y-%m-%d"))
        self.all_incidents_summary['month_year_opened'] = self.all_incidents_summary['month_year_opened'].apply(
            lambda x: datetime.date.strftime(x, "%Y-%m-%d"))
        self.all_incidents_summary['creation_tstamp'] = self.all_incidents_summary['creation_tstamp'].apply(
            lambda x: datetime.datetime.strftime(x, "%Y-%m-%d %H:%M:%S"))

        def resolution_tstamp_convert(value):
            try:
                return datetime.datetime.strftime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

        self.all_incidents_summary['resolution_tstamp'] = self.all_incidents_summary['resolution_tstamp'].apply(lambda x: resolution_tstamp_convert(x))

    def summarise_raised(self, input_data):
        input_data['clean_date'] = input_data['creation_tstamp'].dt.date
        input_data['month_year'] = input_data['creation_tstamp'].to_numpy().astype('datetime64[M]')

        summary_data = input_data.groupby(['month_year', 'clean_date', 'customer_company_group'], as_index=False).agg(
            total_raised=pd.NamedAgg(column='incident_code', aggfunc='count'),
            P1_raised=pd.NamedAgg(column='priority', aggfunc=lambda x: (x == 'Crítica').sum()),
            P2_raised=pd.NamedAgg(column='priority', aggfunc=lambda x: (x == 'Alta').sum()),
            P3_raised=pd.NamedAgg(column='priority', aggfunc=lambda x: (x == 'Media').sum()),
            P4_raised=pd.NamedAgg(column='priority', aggfunc=lambda x: (x == 'Baja').sum())
        )

        summary_data['month_year'] = summary_data['month_year'].apply(lambda x: datetime.date.strftime(x, "%Y-%m-%d"))
        summary_data['clean_date'] = summary_data['clean_date'].apply(lambda x: datetime.date.strftime(x, "%Y-%m-%d"))
        return summary_data

    def summarise_incidents(self, incident_data):
        columns_to_keep = ['incident_code', 'clean_date', 'month_year_opened', 'month_year_closed', 'customer_company_group', 'department_name',
                           'department_code', 'department_desc', 'creation_tstamp',
                           'resolution_tstamp', 'priority', 'inc_type', 'time_to_resolution',
                           'sla_threshold', 'sla_met', 'backlog_indicator']

        incident_data['clean_date'] = incident_data['creation_tstamp'].dt.date
        incident_data['month_year_opened'] = incident_data['creation_tstamp'].to_numpy().astype('datetime64[M]')
        incident_data['month_year_closed'] = incident_data['resolution_tstamp'].to_numpy().astype('datetime64[M]')
        incident_data['time_to_resolution'] = (
                    incident_data['resolution_tstamp'] - incident_data['creation_tstamp']).astype('timedelta64[h]')

        incident_data['sla_threshold'] = incident_data['priority'].apply(lambda x: self.__SLA_THRESHOLDS[x])

        incident_data.loc[incident_data['time_to_resolution'] <= incident_data['sla_threshold'], 'sla_met'] = True
        incident_data.loc[incident_data['time_to_resolution'] > incident_data['sla_threshold'], 'sla_met'] = False
        incident_data.loc[incident_data['resolution_tstamp'].isna(), 'sla_met'] = None

        incident_data = incident_data.apply(self.split_client_dept, axis=1)

        final_data = incident_data[columns_to_keep]
        return final_data

    def convert_dates(self, df, cols_to_convert):
        for column in cols_to_convert:
            df[column] = df[column].apply(lambda x: self.time_convert(x, coltype='tstamp'))

        return df

    def time_convert(self, input, coltype):
        if coltype == 'tstamp':
            try:
                return datetime.datetime.strptime(str(input), '%d/%m/%Y %H:%M')
            except ValueError:
                return None
        elif coltype == 'date':
            try:
                return datetime.datetime.strptime(str(input), '%d/%m/%Y')
            except ValueError:
                return None

    def split_client_dept(self, row):
        if isinstance(row['client_dept'], str):
            string_to_split = row['client_dept']
            string = string_to_split.replace(')', ' (')
            split_list = string.split(" (")

            row['department_desc'] = split_list[0]
            row['department_code'] = split_list[1]

            if split_list[1] in self.__CODES_TO_DEPT:
                row['department_name'] = self.__CODES_TO_DEPT[split_list[1]]
            else:
                row['department_name'] = None

        else:
            row['department_desc'] = None
            row['department_code'] = None
            row['department_name'] = None

        return row

