# class Utilities:
#     @staticmethod
#     def get_domain_name(url):
#         url = url.rstrip('/')
#         url = url.rstrip('#')
#         url = url.rstrip('/')
#         url = url.replace('http://', '')
#         url = url.replace('https://', '')
#         url = url.replace('www.', '')
#         url = url.strip()
#         url = url.lower()
#         res = url.split('/')
#         url = res[0].strip()
#         url = url.split(":")[0].strip()
#         return url
#
#     @staticmethod
#     def construct_cla_from_dict(query_dict):
#         if len(query_dict) > 0:
#             for key, value in query_dict.items():
#                 if key.__contains__("start_dt"):
#                     xw = 'where ' + str(key) + " " + ">= " + "'" + str(value)
#                     print(xw)
#                 else:
#                     where = "where" + str(key) + " regexp'(^|[[:space:]])" + str(value) + "([[:space:]]|$)' "
#                 return xw
#         else:
#             return False
