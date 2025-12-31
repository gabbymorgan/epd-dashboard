import asyncio

async def scan_for_seconds(seconds: int):
    scan_process = await asyncio.create_subprocess_shell(
        f'bluetoothctl --timeout {seconds} scan on', stdout=asyncio.subprocess.PIPE)
    await scan_process.wait()
    stdout, stderr = await scan_process.communicate()
    output = stdout.decode().split("\n")
    return output

async def connect_to_device(device_id):
    connect_process = await asyncio.create_subprocess_shell(
        f'bluetoothctl connect {device_id}', stdout=asyncio.subprocess.PIPE)
    await connect_process.wait()
    stdout, stderr = await connect_process.communicate()
    output = stdout.decode().split("\n")
    return(output[-2])

# async def pair_with_device(device_id):
#     pair_process = await asyncio.create_subprocess_shell(
#         f'bluetoothctl pair {device_id}', stdout=asyncio.subprocess.PIPE)
#     await pair_process.wait()
#     stdout, stderr = await pair_process.communicate()
#     output = stdout.decode().split("\n")
#     print(output[-2])

# async def disconnect_from_device(device_id):
#     disconnect_process = await asyncio.create_subprocess_shell(
#         f'bluetoothctl disconnect {device_id}', stdout=asyncio.subprocess.PIPE)
#     stdout, stderr = await disconnect_process.communicate()
#     output = stdout.decode().split("\n")
#     return output

# async def remove_device(device_id):
#     removal_process = await asyncio.create_subprocess_shell(
#         f'bluetoothctl remove {device_id}', stdout=asyncio.subprocess.PIPE)
#     stdout, stderr = await removal_process.communicate()
#     output = stdout.decode().split("\n")
#     return output

async def get_available_devices(paired=False, connected=False):
    command = 'bluetoothctl devices'
    if paired:
        command += " Paired"
    elif connected:
        command += " Connected"
    get_devices_process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE)
    await get_devices_process.wait()
    stdout, stderr = await get_devices_process.communicate()
    output = stdout.decode().split("\n")
    device_list = []
    for line in output:
        terms = line.split(" ")
        if terms[0] == "Device":
            name = " ".join(terms[2:])
            value = terms[1]
            device_list.append({"name": name, "value": value})
    return device_list