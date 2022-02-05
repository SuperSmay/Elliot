import threading
import concurrent.futures

num_list = [1,2,3,0,4,5,6,7,8,9,10]
1,2,3,4,5,6,7,8,9,10

def loading_loop():
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(print_thing, num) for num in num_list]
            for future in concurrent.futures.as_completed(futures):
                try:
                    output = future.result()
                    print(output)
                except ZeroDivisionError:
                    print('ope')
        print('All done')

def print_thing(number):
    print(f'Number: {number} 5/Number: {5/number}')
    return f'Completed for {number}'

loading_loop()