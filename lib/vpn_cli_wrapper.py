import asyncio

from lib.exec_with_expect import sudo_exec


class VpnCliWrapper(object):

    EXE_NAME = 'adguardvpn-cli'
    BOLD_START = '\033[1m'
    BOLD_END = '\033[0m'

    def __init__(self):
        code, path, _ = asyncio.run(self.find_client())
        self.executable = path

    async def run_cmd(self, cmd, password=None):
        if password:
            run_cmd = ['echo', f"'{password}'", '|', 'sudo', '-S', 'pwd', ';']
            run_cmd.extend(cmd)
            cmd = run_cmd

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        code = proc.returncode
        out = stdout.decode().strip()
        err = stderr.decode().strip()

        cmd_txt = ' '.join(cmd)

        # print(
        #     f'======================'
        #     f'\nCMD: "{" ".join(cmd)}"'
        #     f'\nCode: {code}'
        #     f'\nstdout: {out}'
        #     f'\nstderr: {err}'
        #     f'\n======================'
        # )

        assert code == 0, f'Error occurred while running {cmd_txt}'

        return code, out, err

    async def find_client(self):
        cmd = ['which', self.EXE_NAME]
        return await self.run_cmd(cmd)

    async def list_locations(self):
        cmd = [self.executable, 'list-locations']
        code, locations, _ = await self.run_cmd(cmd)

        locations = locations.splitlines()
        locations = [line.strip(self.BOLD_START).strip(self.BOLD_END).strip() for line in locations]
        locations = locations[1:-2]
        locations = '\n'.join(locations)

        return locations

    async def vpn_status(self):
        cmd = [self.executable, 'status']
        code, status, _ = await self.run_cmd(cmd)
        status = status.splitlines()[0]
        return status

    async def vpn_start(self, location, password):
        cmd = f'{self.executable} connect -l "{location}"'
        out = await sudo_exec(cmd, password)

    async def vpn_stop(self):
        cmd = [self.executable, 'disconnect']
        code, out, _ = await self.run_cmd(cmd)


if __name__ == '__main__':
    wrapper = VpnCliWrapper()
    asyncio.run(wrapper.list_locations())
    asyncio.run(wrapper.vpn_status())
    # asyncio.run(wrapper.vpn_start('EE', 'password'))
    # time.sleep(10)
    # asyncio.run(wrapper.vpn_stop())
