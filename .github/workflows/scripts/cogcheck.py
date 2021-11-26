import asyncio
import os

from aiohttp_json_rpc import JsonRpcClient
from dotenv import load_dotenv

CHECK = "✔"
CROSS = "❌"

load_dotenv()  # does not override if already set (ie running in workflow)

workspace = os.environ.get("GITHUB_WORKSPACE")
discord_token = os.environ.get("DISCORD_BOT_TOKEN")
separator = os.environ.get("SEP") or ";"


async def main():
    red_proc = await asyncio.create_subprocess_shell(
        f"redbot --no-instance --token {discord_token} --prefix ! --rpc",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace,
    )
    print("Started Red. Waiting for Red to be ready...")

    await asyncio.sleep(15)  # let red start (yes i could do it dynamically....)

    client = JsonRpcClient()
    await client.connect("localhost", 6133)

    print("Attempting to load cogs.")
    try:
        outcomes: dict = await client.call(
            "CORE__LOAD",
            [
                [
                    "aliases",
                    "anotherpingcog",
                    "beautify",
                    "betteruptime",
                    "cmdlog",
                    "ghissues",
                    "github",
                    "googletrends",
                    "madtranslate",
                    "stattrack",
                    "status",
                    "system",
                    "timechannel",
                    "wol",
                ]
            ],
        )
    finally:
        await client.disconnect()

    red_proc.terminate()

    message = ""
    exit_code = 0
    if loaded := outcomes.get("loaded_packages"):
        message += f"{CHECK} {', '.join(loaded)} ({len(loaded)}) successfully loaded.\n"
    if failed := outcomes.get("failed_packages"):
        message += f"{CROSS} {', '.join(failed)} ({len(failed)}) failed to load.\n"
        exit_code = 1
    if notfound := outcomes.get("notfound_packages"):
        message += (
            f"{CROSS} {', '.join(notfound)} ({len(notfound)}) failed to load because they "
            "could not be found.\n"
        )
        exit_code = 1
    if failed_with_reason := outcomes.get("failed_with_reason"):
        message += (
            f"{CROSS} {', '.join(failed_with_reason)} ({len(failed_with_reason)}) failed "
            "to load because they raised CogLoadError.\n"
        )
        exit_code = 1

    # not checking invalid_pkg_names, alreadyloaded_packages, repos_with_shared_libs

    print(message)
    exit(exit_code)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
