def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False
    return True

def next_prime(num):
    next_number = num + 1
    while not is_prime(next_number):
        next_number += 1
    return next_number

def previous_prime(num):
    previous_number = num - 1
    while previous_number > 1 and not is_prime(previous_number):
        previous_number -= 1
    return previous_number

input_number = int(input('Enter a number: '))
print('Is prime:', is_prime(input_number))
print('Next prime:', next_prime(input_number))
print('Previous prime:', previous_prime(input_number))
