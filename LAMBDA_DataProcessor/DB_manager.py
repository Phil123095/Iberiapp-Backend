import connection as connector
from pangres import upsert


class DBManager:
    def __init__(self):
        self.connection = connector.get_db_connections()

    def report_to_db(self, processed_report):
        incidents_summary = processed_report.all_incidents_summary
        raised_summary = processed_report.raised_summary

        raised_summary.set_index(['clean_date', 'customer_company_group'], inplace=True)
        incidents_summary.set_index(['incident_code'], inplace=True)

        upsert(con=self.connection,
               df=processed_report.raised_summary,
               table_name='summary_raised',
               if_row_exists='update')

        upsert(con=self.connection,
               df=incidents_summary,
               table_name='summary_all_incidents',
               if_row_exists='update')

