def calculate_checksum(data):
    if len(data) % 2 != 0:
        data += b'\0'
    sum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        sum += word
        if sum > 0xFFFF:
            sum = (sum & 0xFFFF) + 1
    checksum = ~sum & 0xFFFF
    return checksum

def verify_checksum(data, checksum):
    if len(data) % 2 != 0:
        data += b'\0'
    sum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        sum += word
        if sum > 0xFFFF:
            sum = (sum & 0xFFFF) + 1
    sum += checksum
    if sum > 0xFFFF:
        sum = (sum & 0xFFFF) + 1
    return sum == 0xFFFF

def run_tests():
    test_data = b'Hello, World!'
    checksum = calculate_checksum(test_data)
    print(f"Test 1: Correct data")
    print(f"Data: {test_data}")
    print(f"Checksum: {checksum}")
    print(f"Verification: {verify_checksum(test_data, checksum)}")
    print()

    test_data_corrupted = b'Hello, Worl!'
    print(f"Test 2: Corrupted data")
    print(f"Data: {test_data_corrupted}")
    print(f"Checksum: {checksum}")
    print(f"Verification: {verify_checksum(test_data_corrupted, checksum)}")
    print()

    test_data_empty = b''
    checksum_empty = calculate_checksum(test_data_empty)
    print(f"Test 3: Empty data")
    print(f"Data: {test_data_empty}")
    print(f"Checksum: {checksum_empty}")
    print(f"Verification: {verify_checksum(test_data_empty, checksum_empty)}")
    print()

if __name__ == "__main__":
    run_tests()