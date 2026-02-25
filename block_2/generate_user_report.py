import pandas as pd

df = pd.read_csv('./work/user_actions.csv')

# Необходимо привести столбец event_time к нужному формату
df['event_time'] = pd.to_datetime(df['event_time'])

# Количество view, click, purchase по каждому пользователю
new_df = df[['user_id', 'event_type']]
pivot_new_df = new_df.pivot_table(
    index='user_id',
    columns='event_type',
    aggfunc='size',
    fill_value=0
).reset_index()

# Средний интервал между действиями каждого пользователя
df_avg = df.sort_values(['user_id', 'event_time'])
df_avg['avg'] = df.groupby('user_id')['event_time'].diff()
df_avg_user = df_avg.groupby('user_id')['avg'].mean().reset_index()

# Время первой и последней активности
df_first_event = df.sort_values(['user_id', 'event_time'])

#first_event
df_first_event = df_first_event.groupby('user_id')['event_time'].min().reset_index()
df_first_event.columns = ['user_id', 'first_event']

#last_event
df_last_event = df.sort_values(['user_id', 'event_time'])
df_last_event = df_last_event.groupby('user_id')['event_time'].max().reset_index()
df_last_event.columns = ['user_id', 'last_event']

# Создание таблицы
user_report = df_2.join(df_avg_user['avg'])
user_report = user_report.join(df_first_event['first_event'])
user_report = user_report.join(df_last_event['last_event'])

#Сохраняем таблицу
user_report.to_csv('user_report.csv', sep=',', index=False)


