list_name = ''
list_to_add_to = []


def generate_str():
    base_str = list_name
    list_str = ",\n".join([f'    "{item}"' for item in list_to_add_to])
    return f"{base_str} = [\n{list_str}\n] "
    
list_name = input("List name: ")
try:
    while True:
        next_item = input("Next item: ")
        list_to_add_to.append(next_item)

except KeyboardInterrupt:
    print()
    print(generate_str())