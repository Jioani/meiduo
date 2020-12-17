from celery import Celery

celery_app = Celery("demo")
celery_app.conf.broker_url = "redis://192.168.19.131:6379/3"


@celery_app.task(name="send_sms_code")
def send_sms_code(mobile, sms_code):
    print("发送短信的任务函数被调用")
    print("[mobile: %s]  [sms_code: %s]" % (mobile, sms_code))
