import list_api

if __name__ == "__main__":
    session = list_api.login("example@acme.com", "password")

    # courses = list_api.get_all_courses(session)
    # print(courses)

    # for p in list_api.get_problems_for_course(session, 155):
    #     print(p)

    # with open("solution.zip", "rb") as f:
    #     byte_data = f.read()
    #     list_api.submit_solution(session, 5479, byte_data)

    # list_api.run_test_for_submit(session, 5479, 2)
