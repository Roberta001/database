from datetime import date, timedelta

def get_last_census_date(today: date = date.today()) -> date:
    last_weekly_census_date = today - timedelta(days=(today.weekday()-5)%7)
    last_monthly_census_date = today.replace(day=1)
    return max(last_weekly_census_date, last_monthly_census_date)

