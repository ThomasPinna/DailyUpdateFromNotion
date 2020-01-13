# Daily Updates:

## The concept

Daily update is a mechanism for some sort of digital standup. There are some advantages of doing this digital:

- it enables remote work
- it enables automation

This script is helping with the automation part. In our daily update we share what we've been working on and what we plan to do the coming day. This information can be collected from my notion task management system.

For this script to work, you need a task table, 

- with a `Status` field of which the values can be `Done` or `Done yesterday` 
- Every task needs an `archived` checkbox (tasks where archived is checked will be ignored). 
- Every tasks needs to have a `Assigned to` field, which will also be used for the filter

## How to install

- download the script somewhere

- install dependencies

  ```shell
  pip install notion
  pip install slack
  ```

- add a function to your `.zshrc` (or equivalent) like this:

  ```bash
  daily_update() {command python3 /location/of/daily_updates.py $@}
  ```

## How to run

This tool needs some keys and some details in order to run successfully. You have two options, they 
can be used interchangeably.

### Command line options

```help
Usage: daily_updates.py [OPTIONS]

Options:
  --user TEXT          Your notion user id  [required]
  --channel TEXT       The slack channel where the message should be posted (without #) [required]
  --notion-table TEXT  The notion table containing the tasks [required]
  --slack-key TEXT     A slack authentication key [required]
  --notion-key TEXT    The notion authentication key [required]
  --help               Show this message and exit.
``` 

###  Environment variables

example configuration:
```bash
export du_notion_table="https://www.notion.so/mycellhub/2c9112bb9586478fbba2f1e1eba15c9e?v=557b0e9d6bc743fb84733628d7cfa6c2"
export du_slack_channel="daily_updates"
export du_user_id="41d1a012-7c6f-49a3-8e80-acdcddb3c92b"
export du_slack_key=$slack_key
export du_notion_key=$notion_key
```

## Todo

- [ ] Mark items that where done yesterday as done after posting
- [x] Make the following things parameters of the script (or environment variables)
  - [x] user id
  - [x] table url
  - [x] slack channel
- [ ] Make it easier to support other Status fields (and support a variable amount of them)
- [ ] Make user filtering and archived filtering optional
- [ ] Allow using user name instead of user id
- [ ] Make the package pip installable
