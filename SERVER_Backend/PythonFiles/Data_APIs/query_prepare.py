def create_conditionals(start_date, end_date, customer_group, granularity):
    # Create Conditional Statement for Date Timeframe
    if start_date == end_date:
        condition = f"a.month_year = '{start_date}'"
        mttr_condition = f"a.month_year_closed = '{start_date}'"
        dept_raised_condition = f"a.month_year_opened = '{start_date}'"

    else:
        condition = f"month_year between '{start_date}' and '{end_date}'"
        mttr_condition = f"month_year_closed between '{start_date}' and '{end_date}'"
        dept_raised_condition = f"month_year_opened between '{start_date}' and '{end_date}'"

    # Create Customer Company Group Conditional
    if len(customer_group) == 1:
        cust_condition = f"= '{customer_group[0]}'"
    else:
        cust_condition = f"""in ({",".join("'" + x + "'" for x in customer_group)})"""

    # Create Granularity Conditional:
    if granularity == 'day':
        gran_condition = 'b.date'
    elif granularity == 'week':
        gran_condition = 'b.week_date'
    elif granularity == 'month':
        gran_condition = 'b.month_date'
    else:
        gran_condition = 'b.date'

    return condition, mttr_condition, cust_condition, dept_raised_condition, gran_condition


def prepare_queries(start_date, end_date, customer_group, granularity):
    date_condition, mttr_date_condition, cust_condition, dept_raised_condition, granularity_condition = create_conditionals(
        start_date, end_date, customer_group, granularity)

    query_summaries_TS = f"""
    with start as (
        select 
            {granularity_condition} as agg_date,
            sum(P4_raised) as P4_raised,
            sum(P3_raised) as P3_raised,
            sum(P2_raised) as P2_raised,
            sum(P1_raised) as P1_raised
        from summary_raised as a
        left join calendar_table as b
            on a.clean_date = b.date
        where {date_condition} and customer_company_group {cust_condition}
        group by 1
        order by clean_date asc)
    select 
        date_format(agg_date, '%d-%m-%Y') as clean_date, 
        P1_raised,
        P2_raised,
        P3_raised,
        P4_raised
    from start
    """

    query_summaries = f"""select 
            sum(total_raised) as total_raised,
            sum(P1_raised) as P1_raised,
            sum(P2_raised) as P2_raised,
            sum(P3_raised) as P3_raised,
            sum(P4_raised) as P4_raised
        from summary_raised
        where {date_condition} and customer_company_group {cust_condition}"""

    mttr_query = f"""with final as (
            select 
                priority, 
                case 
                    when priority = 'Crítica' then 1 
                    when priority = 'Alta' then 2
                    when priority = 'Media' then 3 
                    when priority = 'Baja' then 4 
                end as priority_rank,
                sla_met,
                round(avg(time_to_resolution), 2) as mttr
            from summary_all_incidents
            where backlog_indicator = 'closed' and {mttr_date_condition} and customer_company_group {cust_condition}
            group by 1,2,3
            order by priority_rank asc)

            select 
                case when priority = 'Crítica' then 'Critical'
                    when priority = 'Alta' then 'High'
                    when priority = 'Media' then 'Medium'
                    when priority = 'Baja' then 'Low'
                end as priority,
                case 
                    when sla_met = 0 then 'SLA not met'
                    when sla_met = 1 then 'SLA met'
                end as sla_indicator,
                mttr 
            from final 
            order by priority_rank asc"""

    query_mttr_perc = f"""
            with start as (
            select 
                priority,
                count(distinct(incident_code)) as total_incidents
            from summary_all_incidents
            where backlog_indicator = "closed" and {mttr_date_condition} and customer_company_group {cust_condition}
            group by 1 
            )

            select 
                case when a.priority = 'Crítica' then 'Critical'
                    when a.priority = 'Alta' then 'High'
                    when a.priority = 'Media' then 'Medium'
                    when a.priority = 'Baja' then 'Low'
                end as priority,
                100*(sum(case when sla_met = 1 then 1 end)/b.total_incidents) as SLA_met_vals,
                100*(sum(case when sla_met = 0 then 1 end)/b.total_incidents) as SLA_not_met_vals
            from summary_all_incidents as a 
            left join start as b
                on a.priority = b.priority 
            where backlog_indicator = "closed" and {mttr_date_condition} and customer_company_group {cust_condition}
            group by 1
            order by b.total_incidents asc
            """

    department_raised = f"""
        with start as (
            select 
                {granularity_condition} as agg_date,
                case 
                    when department_name is null then "No Department Specified"
                    else department_name 
                end as name,
                count(distinct incident_code) as total_incidents, 
                sum(case when priority = 'Crítica' then 1 else 0 end) as P1_raised,
                sum(case when priority = 'Alta' then 1 else 0 end) as P2_raised,
                sum(case when priority = 'Media' then 1 else 0 end) as P3_raised,
                sum(case when priority = 'Baja' then 1 else 0 end) as P4_raised
            from summary_all_incidents as a
            left join calendar_table as b 
                on a.clean_date = b.date
            where {dept_raised_condition} and customer_company_group {cust_condition}
            group by 1, 2
            order by 1 asc, 3 desc)
            select 
                date_format(agg_date, '%d-%m-%Y') as clean_date, 
                name,
                total_incidents,
                P1_raised,
                P2_raised,
                P3_raised,
                P4_raised
            from start
        """

    query_causes_ts = f"""
    with start as (
        select 
            {granularity_condition} as agg_date,
            inc_type as name, 
            count(distinct incident_code) as total_incidents, 
            sum(case when priority = 'Crítica' then 1 else 0 end) as P1_raised,
            sum(case when priority = 'Alta' then 1 else 0 end) as P2_raised,
            sum(case when priority = 'Media' then 1 else 0 end) as P3_raised,
            sum(case when priority = 'Baja' then 1 else 0 end) as P4_raised
        from summary_all_incidents as a
            left join calendar_table as b 
                on a.clean_date = b.date
        where {dept_raised_condition} and customer_company_group {cust_condition}
        group by 1, 2
        order by 1 asc, 3 desc)
        select 
            date_format(agg_date, '%d-%m-%Y') as clean_date, 
            name,
            total_incidents,
            P1_raised,
            P2_raised,
            P3_raised,
            P4_raised
        from start
    """

    query_dictionary = {
        'summary_data': query_summaries,
        'raised_TS_prio': query_summaries_TS,
        'mttr_data': mttr_query,
        'mttr_perc': query_mttr_perc,
        'department_raised_TS': department_raised,
        'cause_raised_TS': query_causes_ts
    }

    return query_dictionary
