# INCS2 Bot - Localization system

If you want to contribute - make sure that translation into your preferred language is not complete yet by looking at [Progress](#progress) section.
Then check [Contributing](#contributing) section to know how to start translating

---

### Progress

Here you can see translations' progress and contributors' list:

|      | Language     |    Progress     | Summary  | Contributors |
|:----:|--------------|:---------------:|:--------:|--------------|
| :gb: | English (en) | ██████████ 100% | built in |              |
| :ru: | Russian (ru) | ██████████ 100% | built in |              |

### Contributing

1. Fork this repository.
2. Clone forked repository using Git.
3. In Git, create a new repository branch and checkout to it.
4. Open the repository folder. In `l10n/data/` folder, find prefered lang file.
    - If there is no such file, you can create it with Python.
        <details>
        <summary>Here is how:</summary>

        > 1. In `l10n/` folder create a Python file and paste this code:
        >
        >    ``` python
        >    from l10n import L10n
        >     
        >    lang_code = ''  # here you need to insert ISO 639-1 lang code
        >    L10n.create_lang_file('data', lang_code)
        >    ```
        >
        > 2. Set `lang_code` variable to ISO 639-1 code of prefered language.  
        >    - [List of ISO 639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
        >
        > 3. Run the script. Your file will be created and placed in `l10n/data/`.  
             When you're done, make sure to delete the script.

        </details>
5. Open the file and start translating it based on string keys and original text.
    - We highly recommend checking the bot functionality to have more text context.
6. You can also add some tags in your language to `tags.json`.
7. Commit and push all the changes.
8. Create a pull request to the original repository and wait for our feedback.
