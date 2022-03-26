try:
    import SERVER_Backend.PythonFiles.Data_APIs.query_prepare as query_prep
    import SERVER_Backend.PythonFiles.Data_APIs.out_data_processing as dataclean
except ModuleNotFoundError:
    import Data_APIs.query_prepare as query_prep
    import Data_APIs.out_data_processing as dataclean

import pandas as pd


def get_data(connection, start_date, end_date, customer_company_group, granularity):
    query_dict = query_prep.prepare_queries(start_date=start_date, end_date=end_date, customer_group=customer_company_group, granularity=granularity)

    final_data = {}
    for item, query in query_dict.items():
        if item == 'summary_data':
            formatted_data = dataclean.convert(pd.read_sql(query, connection).to_dict(orient='records')[0])

        if item in ['all_raised_data', 'raised_TS_prio', 'mttr_perc']:
            formatted_data = pd.read_sql(query, connection).to_dict(orient='list')

        if item == 'mttr_data':
            formatted_data = dataclean.transform_mttr(pd.read_sql(query, connection))

        elif item == 'cause_raised_TS' or item == 'department_raised_TS':
            TS, totals = dataclean.transform_cause_TS(pd.read_sql(query, connection))
            formatted_data = TS
            final_data[item.replace('_TS', '_total')] = totals

        final_data[item] = formatted_data

    return final_data
