from app import db, jidouka, definition, QuestionAndAnswer, User

db.create_all()

# jidou1 = jidouka(innovation_name='Tự động thống kê công việc',
#                  task_type='quy trình làm việc',
#                  tool='Word+Excel+PandasPython',
#                  describe_innovation='Dùng công cụ thống kê pandas kết hợp excel để thống kê kết quả công việc',
#                  software='Word, Excel, VisualStudio',
#                  product='File excel. File word',
#                  pic='Nguyễn Văn D',
#                  dc='DC5',
#                  num_tasks=1,
#                  saved_hours=28,
#                  information='Link tài liệu triển khai: \
#                  +) Video: https:\\youtube.vn \
#                 +) File Powerpoint: powerpoint.pw')

# jidou2 = jidouka(innovation_name='Tự động phân tích',
#                  task_type='Phân tích',
#                  tool='Excel+Python',
#                  describe_innovation='Dùng code để tự viết dữ liệu',
#                  software='Excel',
#                  product='File xlsx',
#                  pic='Nguyễn Văn A',
#                  dc='DC1',
#                  num_tasks=2,
#                  saved_hours=20,
#                  information= 'Link tài liệu triển khai: \
#                 +) Video: https:\\youtube.vn \
#                 +) File Powerpoint: powerpoint.pw' )

# jidou3 = jidouka(innovation_name='Cải tiến quy trình làm việc',
#                  task_type='Working',
#                  tool='Python',
#                  describe_innovation='Tự động cải thiện quy trình làm việc nhanh gọn',
#                  software='Window',
#                  product='File các loại',
#                  pic='Nguyễn Văn E',
#                  dc='DC7',
#                  num_tasks=2,
#                  saved_hours=12,
#                  information='Link tài liệu triển khai: \
#                 +) Video: https:\\youtube.vn \
#                 +) File Powerpoint: powerpoint.pw')



# db.session.add_all([jidou1,jidou2,jidou3])
# db.session.commit()
