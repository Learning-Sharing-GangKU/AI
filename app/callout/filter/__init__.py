'''
app/callout/filter/registry.py
환경변수를 기반으로 한 번만 xlmr_client 생성 후 싱글톤으로 전역에 보관
처음에 main에서 init_xlmr_client() 함수로 해당 xlmr_client로 초기화
그 후에는 get_xlmr_client()로 접근해서 xlmr을 사용할 수 있도록한다.
'''

'''
xlmr 외부 API 실제 제공자, 해당 파일의 predict를 사용해서 해당 text가 독성을 가지고 있는지 판단.
'''
