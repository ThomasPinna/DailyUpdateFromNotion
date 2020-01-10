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

## How to use

- download the script somewhere

- install dependencies

  ```shell
  pip install notion
  pip install slack
  ```

  

- add a function to your `.zshrc` (or equivalent) like this:

  ```bash
  daily_update() {command python3 /location/of/daily_updates.py }
  ```

- Setup api keys as environment variables:

  - `notion_key`
  - `slack_key`

- In the script, change your user id

## Todo

- mark items that where done yesterday as done after posting
- Make it easier to support other tables structures
- Make it easier to define the user id (environment variable or parameter)
- Make the package installable 