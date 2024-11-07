

def format_table_for_chatbot(df):
    new_df = df[['innovation_name','task_type','tool','software','product','contributor','dc']]
    new_df.rename(columns={'innovation_name':'Tên cải tiến', 'task_type':'Loại hình công việc','tool':'Công cụ','software':'Phần mềm','product':'Sản phẩm','contributor':'Tác giả','dc':'Design Center'}, inplace=True)
    return new_df

def format_result_tapas(result):
    lst = []
    num = 0
    if result.startswith('SUM'):
        result = result[6:]
        lst= result.split(',')
        for i in lst:
            num += float(i)
        result = str(num)
    elif result.startswith('AVERAGE'):
        result = result[10:]
        lst= result.split(',')
        for i in lst:
            num += float(i)
        num /= len(lst)
        result = str(num)
    elif result.startswith('COUNT'):
        result = result[8:]
        lst = set(result.split(','))
        num = len(lst)
        result = int(num)
    return result