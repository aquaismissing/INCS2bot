# INCS2 Bot - Localization system

If you want to contribute - make sure that translation into your preferred language is not complete yet by looking at [Progress](#progress) section.
Then check [Contributing](#contributing) section to know how to start translating

---

## Progress

Here you can see translations' progress and contributors' list:

| Code | Language     |    Progress     |             Summary              |        Contributors        |
|:----:|--------------|:---------------:|:--------------------------------:|:--------------------------:|
|  gb  | English      | ██████████ 100% |             built in             |                            |
|  ru  | Russian      | ██████████ 100% |             built in             |                            |
|  fa  | Persian      | █████████▒ 90%  |         settings missing         |    [@A460N] (telegram)     |
|  tr  | Turkish      | ████████▒▒ 80%  |      settings, tags missing      |   [@ITMiroN] (telegram)    |
|  uz  | Uzbek        | ████████▒▒ 80%  | user gamestats, settings missing |   [@d1az1337] (telegram)   |
|  uk  | Ukrainian    | ██████████ 100% |            fully done            | [akimerslys], [Agent47Dev] |
|  be  | Belarusian   | ██████████ 100% |            fully done            |       [HiddenDeath]        |
|  it  | Italian      | █████████▒ 90%  |            fully done            |         [MrJiavo]          |

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
