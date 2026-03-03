import asyncio
import platform, os, logging
import pexpect

log = logging.getLogger(__name__)

async def sudo_exec(cmdline, passwd):
    osname = platform.system()
    if osname == 'Linux':
        prompt = r'\[sudo\] password for %s: ' % os.environ['USER']

    elif osname == 'Darwin':
        prompt = 'Password:'

    else:
        assert False, osname

    child = pexpect.spawn(cmdline)
    idx = child.expect([prompt, pexpect.EOF], 3)
    if idx == 0:
        log.debug('sudo password was asked.')
        child.sendline(passwd)
        child.expect('Connected to')
        # child.expect(pexpect.EOF)

    return child.before


if __name__ == '__main__':
    asyncio.run(sudo_exec('adguardvpn-cli connect -l EE', 'password'))
