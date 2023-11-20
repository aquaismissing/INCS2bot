# INCS2 Bot - Localization system

If you want to contribute - make sure that translation into your preferred language is not complete yet by looking at [Progress](#progress) section.
Then check [Contributing](#contributing) section to know how to start translating

---

## Progress

Here you can see translations' progress and contributors' list:

| Code | Language     |    Progress     |                             Summary                              |        Contributors        |
|:----:|--------------|:---------------:|:----------------------------------------------------------------:|:--------------------------:|
|  en  | English      | ██████████ 100% |                             built in                             |                            |
|  ru  | Russian      | ██████████ 100% |                             built in                             |                            |
|  ar  | Arabic       | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  be  | Belarusian   | ████████▒▒ 80%  |                     missing: leaderboard, USA DC                 |       [HiddenDeath]        |
|  da  | Danish       | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  de  | German       | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  es  | Spanish      | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  fa  | Persian      | ████████▒▒ 80%  |               missing: settings, leaderboard, USA DC             |          [@A460N]          |
|  fi  | Finnish      | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  fr  | French       | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  hi  | Hindi        | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  it  | Italian      | ████████▒▒ 80%  |                      missing: leaderboard, USA DC                |          [MrJiavo]         |
|  ja  | Japanese     | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  no  | Norwegian    | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  pl  | Polish       | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  pt  | Portuguese   | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  sv  | Swedish      | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |
|  tr  | Turkish      | ███████▒▒▒ 70%  |           missing: settings, leaderboard, tags, USA DC           |         [@ITMiroN]         |
|  uk  | Ukrainian    | ████████▒▒ 80%  |                     missing: leaderboard, USA DC                 | [akimerslys], [Agent47Dev] |
|  uz  | Uzbek        | ███████▒▒▒ 70%  |       missing: user game stats, settings, leaderboard, USA DC    |         [@d1az1337]        |
|  zh  | Chinese      | ▒▒▒▒▒▒▒▒▒▒ 0%   |                        contributors needed                       |                            |


## Contributing 

### Prerequirements

- GitHub account ([sign up](https://github.com/signup))
- Git ([download](https://git-scm.com/))

### Steps

1. Fork this repository. [100%]
   \
   ![forking repository](../media/fork_repo.png)
2. Open Git Bash and clone the forked repository: `git clone {your fork link}`.
   \
   Then use `cd INCS2bot`.
   \
   ![cloning repository](../media/clone_repo.png)
3. Create a new repository branch and checkout to it using `git checkout -b {branch name}`.
   \
   ![creating branch](../media/create_branch.png)
4. Open the repository folder. In `l10n/data/` folder, find prefered lang file.
   - If there is no such file, you can create it by yourself.
     \
     Just copy `en.json` and rename it with ISO 639-1 code of prefered language (e.g. `de.json`).
      - [List of ISO 639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
5. Open the file and start translating it based on string keys and original text.
   - We highly recommend checking the bot functionality to have more text context.
6. You can also add some tags in your language to `tags.json`.
7. In Git, add new files, then commit and push all the changes.
   \
   ![commiting changes](../media/commit_changes.png)
8. Submit a pull request to the original repository and wait for our feedback.
   \
   ![submiting pull](../media/submit_pull_request.png)


[@A460N]: https://t.me/A460N
[@ITMiroN]: https://t.me/ITMiroN
[@d1az1337]: https://t.me/d1az1337
[akimerslys]: https://github.com/akimerslys
[Agent47Dev]: https://github.com/Agent47Dev
[HiddenDeath]: https://github.com/HiddenDeath
[MrJiavo]: https://github.com/MrJiavo
