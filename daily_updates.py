
# start with some workaround

from notion.collection import (
    _normalize_property_name,
    _normalize_query_list,
    QUERY_RESULT_TYPES,
    QueryResult,
    get_localzone,
)


def new_init(
    self,
    collection,
    collection_view,
    search="",
    type="table",
    aggregate=[],
    filter=[],
    filter_operator="and",
    sort=[],
    calendar_by="",
    group_by="",
):
    self.collection = collection
    self.collection_view = collection_view
    self.search = search
    self.type = type
    self.aggregate = _normalize_query_list(aggregate, collection)
    self.filter = filter
    self.filter_operator = filter_operator
    self.sort = _normalize_query_list(sort, collection)
    self.calendar_by = _normalize_property_name(calendar_by, collection)
    self.group_by = _normalize_property_name(group_by, collection)
    self._client = collection._client


def new_execute(self):

    result_class = QUERY_RESULT_TYPES.get(self.type, QueryResult)

    return result_class(
        self.collection,
        self._client.query_collection(
            collection_id=self.collection.id,
            collection_view_id=self.collection_view.id,
            search=self.search,
            type=self.type,
            aggregate=self.aggregate,
            filter=self.filter,
            sort=self.sort,
            calendar_by=self.calendar_by,
            group_by=self.group_by,
        ),
    )


def new_call_query_collection(
    self,
    collection_id,
    collection_view_id,
    search="",
    type="table",
    aggregate=[],
    filter=[],
    sort=[],
    calendar_by="",
    group_by="",
):

    # convert singletons into lists if needed
    if isinstance(aggregate, dict):
        aggregate = [aggregate]
    if isinstance(sort, dict):
        sort = [sort]

    data = {
        "collectionId": collection_id,
        "collectionViewId": collection_view_id,
        "loader": {
            "limit": 70,
            "loadContentCover": True,
            "query": search,
            "userLocale": "en",
            "userTimeZone": str(get_localzone()),
            "type": type,
        },
        "query": {"aggregate": aggregate, "filter": filter, "sort": sort,},
    }

    response = self._client.post("queryCollection", data).json()

    self.store_recordmap(response["recordMap"])

    return response["result"]


from notion.collection import CollectionQuery
from notion.store import RecordStore

CollectionQuery.__init__ = new_init
CollectionQuery.execute = new_execute
RecordStore.call_query_collection = new_call_query_collection


from notion.client import NotionClient
import slack
import click

# requires environment variables:
#   notion_key
#   slack_key
# the channel and user id to filter on can be customised in the `if __name__=="__main__":` below
# to change the used database, edit the url in connect_with_notion()
# to change the filter for the tasks, edit query_active_tasks_assigned_to
# to change how it is represented or split up, edit string_format
# to change how it is shown in slack, edit message_to_slack_blocks


@click.command()
@click.option(
    "--user", envvar="du_user_id", required=True, help="Your notion user id",
)
@click.option(
    "--channel",
    envvar="du_slack_channel",
    required=True,
    help="The slack channel where the message should be posted (without #)",
)
@click.option(
    "--notion-table",
    envvar="du_notion_table",
    required=True,
    help="The notion table containing the tasks",
)
@click.option(
    "--slack-key",
    envvar="du_slack_key",
    required=True,
    help="A slack authentication key",
)
@click.option(
    "--notion-key",
    envvar="du_notion_key",
    required=True,
    help="The notion authentication key)",
)
def main_process(user, channel, notion_table, slack_key, notion_key):
    # connect with notion
    cv = connect_with_notion(notion_key, notion_table)
    print("connected to notion")
    # retrieve tasks that are active and assigned to user_id
    active_tasks = query_active_tasks_assigned_to(cv=cv, user_id=user)
    print("got relevant tasks")
    # build the message for slack
    in_progress, done_yesterday = string_format(active_tasks)
    slack_blocks = message_to_slack_blocks(done_yesterday, in_progress)
    print("formatted message")
    # send to slack
    push_blocks_to_slack(slack_key, channel, slack_blocks)
    print("tasks posted on slack")


def connect_with_notion(notion_key, notion_table):
    # connect with notion tasks database
    client = NotionClient(token_v2=notion_key, monitor=False)
    return client.get_collection_view(notion_table)


def query_active_tasks_assigned_to(cv, user_id):

    filter_params = (
        {
            "filters": [
                {
                    "filter": {
                        "value": {
                            "type": "exact",
                            "value": {"id": user_id, "table": "notion_user"},
                        },
                        "operator": "person_contains",
                    },
                    "property": "L}(O",
                },
                {
                    "filter": {
                        "value": {"type": "exact", "value": False},
                        "operator": "checkbox_is",
                    },
                    "property": "X*]x",
                },
            ],
            "operator": "and",
        },
    )
    result = list(cv.build_query(filter=filter_params).execute())

    # workaround
    result = [x for x in result if x.assigned_to[0].full_name == "Thomas Pinna"]

    return result


def string_format(active_tasks):
    # if a task is unfinished, return a seedling icon
    unfinished = (
        lambda x: ""
        if len(x.Status) == 1 and x.Status[0] == "done yesterday"
        else ":seedling:"
    )
    # if a task is unpredicted, return a baby icon
    unpredicted = lambda x: ":baby:" if "unplanned" in x.Tags else ""
    # initialise strings
    in_progress = ""
    done_yesterday = ""
    # stringformat every task and add it to the overview strings
    for x in active_tasks:
        print(x.assigned_to[0].full_name)
        url = f'https://www.notion.so/mycellhub/{x.id.replace("-", "")}'
        if "in progress" in x.Status:
            in_progress += f"• <{url}|{x.title}> {unpredicted(x)}\n"

        if "done yesterday" in x.Status:
            done_yesterday += f"• <{url}|{x.title}> {unfinished(x)}{unpredicted(x)}\n"
    return in_progress, done_yesterday


def message_to_slack_blocks(done_yesterday, in_progress):
    return [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*YESTERDAY:*\n{done_yesterday}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*TODAY:*\n{in_progress}"},
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "text": "*Daily Update*  |  _ A :notion: integration_",
                    "type": "mrkdwn",
                }
            ],
        },
    ]


def push_blocks_to_slack(slack_key, channel, blocks):
    # push tasks to slack
    client = slack.WebClient(token=slack_key)

    client.chat_postMessage(channel=f"#{channel}", blocks=blocks, as_user=True)


if __name__ == "__main__":
    main_process()
