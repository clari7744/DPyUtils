# DPyUtils
Some extra discord.py utilities

## Installation:
Linux / macOS / Windows Store:
```sh
python3 -m pip install -U git+https://github.com/clari7744/DPyUtils
```

Windows:
```ps
py -3 -m pip install -U git+https://github.com/clari7744/DPyUtils
```

## Information
<details open>
<summary><strong>Overview:</strong></summary><br>

##### Features:
* Duration utilities
* Context editor: Allows users to edit their message, which will edit the command response.
* Extra converters: 
  * Advanced Converters: Member, User, Role, Color, TextChannel, VoiceChannel, StageChannel, CategoryChannel
  * Added Converters: BotMember, HumanMember, BotUser, HumanUser, NewsChannel, AnyChannel, NonCategoryChannel
* Tasks system: A cog for a to-do list

##### Coming Soon (More details later):
* Debug Cog
* `utils.an`, similar to `utils.s`
</details>

<details>
<summary><strong>Duration Utilities</strong></summary><br>

##### Utilities:
* `duration.DurationParser`: A converter that converts input from `1y1w1d1h1m1s` format to seconds.
* `duration.parse`: Accepts seconds or `datetime.timedelta`, and changes it to a `collections.namedtuple` with each unit in it individually (`duration.ParsedDuration(years=1, weeks=1, days=1, hours=1, minutes=1, seconds=1)`)
* `duration.strfdur`: Accepts seconds, `datetime.timedelta`, or `duration.ParsedDuration` and converts it to a human-readable string.
  - Example: `10000 seconds` -> `2 hours, 46 minutes, and 40 seconds`

##### Usage:
To use the utilities provided in this module, just import `DPyUtils.duration`
</details>

<details>
<summary><strong>Converters</strong></summary><br>


</details>

<details>
<summary><strong>Context Editor</strong></summary><br>


</details>



### Note:
While this repository is meant to be fairly stable, as I have a personal repository that I use for testing and I do plan to only add items to this build once they've been tested and found to be bug-free, I'm not perfect, and there may be some issues. If you do run into any problems while using my tools, please ping me in [my server](https://discord.gg/EQkDnBS) so I can take a look and get that fixed. 
Thank you for your help debugging, and thanks for using my discord.py utilities!

\- @clari7744 💜
