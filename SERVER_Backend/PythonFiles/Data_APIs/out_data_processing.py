def convert(in_dict):
    new_dict_list = []
    for key, value in in_dict.items():
        new_dict_list.append(
            {"key": key,
             "value": value}
        )
    return new_dict_list


def transform_mttr(data):

    newdata = data.pivot(index="priority", columns="sla_indicator", values="mttr")

    final = newdata.to_dict()
    data_order = ['Critical', 'High', 'Medium', 'Low']

    if 'Critical' not in final['SLA not met']:
        final['SLA not met']['Critical'] = 0

    return {
        'labels': data_order,
        'SLA_met_vals': [final['SLA met'][x] for x in data_order],
        'SLA_not_met_vals': [final['SLA not met'][x] for x in data_order]
    }


def transform_cause_TS(data):
    pivot_TS = data.pivot(index="clean_date", columns="name", values="total_incidents").fillna(0)
    pivot_TS.reset_index(inplace=True)
    total_raised = data.groupby(by="name", as_index=False).sum()
    total_raised.sort_values(by="total_incidents", ascending=False, inplace=True)
    return pivot_TS.to_dict(orient="list"), total_raised.to_dict(orient="records")