# flake8: noqa
data = ['()', '(}', '{()()}', '{()((}']

for i in data:
  flag = True
  stack = []
  for j in i:
    if j == '(' or j == '{':
      stack.append(j)
      break

    elif j == ')':
      print(stack[len(stack)-1])
      if stack[len(stack)-1] == '(':
        stack.pop

      else: 
        print(i+": 괄호 짝이 맞지 않습니다.\n")
        flag=False
        break

    elif j == '}':
      print(stack[len(stack)-1])
      if len(stack) != 0 and stack[len(stack)-1] == '{':
        stack.pop

      else: 
        print(i+": 괄호 짝이 맞지 않습니다.\n")
        flag=False
        break

  if(flag):
    print(i+": 괄호 짝이 맞습니다.\n")
