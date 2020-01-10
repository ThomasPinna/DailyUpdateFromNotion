from notion.collection import _normalize_property_name, _normalize_query_list, QUERY_RESULT_TYPES, QueryResult, get_localzone

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
        "query": {
            "aggregate": aggregate,
            "filter": filter,
            "sort": sort,
        },
    }

    response = self._client.post("queryCollection", data).json()

    self.store_recordmap(response["recordMap"])

    return response["result"]

from notion.collection import CollectionQuery
from notion.store import RecordStore
CollectionQuery.__init__ = new_init
CollectionQuery.execute = new_execute
RecordStore.call_query_collection = new_call_query_collection



# Tools to help use notion

from notion.client import NotionClient
import time
import slack
import os

# requires environment variables:
#   notion_key
#   slack_key
# the channel and user id to filter on can be customised in the `if __name__=="__main__":` below
# to change the used database, edit the url in connect_with_notion()
# to change the filter for the tasks, edit query_active_tasks_assigned_to
# to change how it is represented or split up, edit string_format
# to change how it is shown in slack, edit message_to_slack_blocks

def main_process(user_id, channel):
    # connect with notion
    cv = connect_with_notion()
    print('connected to notion')
    print(cv)
    # retrieve tasks that are active and assigned to user_id
    active_tasks = query_active_tasks_assigned_to(cv=cv, user_id=user_id)
    print('got relevant tasks')
    print(active_tasks)
    # build the message for slack
    in_progress, done_yesterday = string_format(active_tasks)
    print(in_progress, done_yesterday)
    slack_blocks = message_to_slack_blocks(done_yesterday, in_progress)
    print('tasks preprocessed')
    # send to slack
    push_blocks_to_slack(channel, slack_blocks)
    print('tasks posted on slack')


def connect_with_notion():
    # connect with notion tasks database
    client = NotionClient(token_v2=os.environ['notion_key'], monitor=False)
    return client.get_collection_view("https://www.notion.so/mycellhub/2c9112bb9586478fbba2f1e1eba15c9e?v=557b0e9d6bc743fb84733628d7cfa6c2")


def query_active_tasks_assigned_to(cv, user_id):
    old_filter_params = [{  
        "id": "e779be32-a7a1-456d-9ad3-aba869b5fbd3",
        "value":{ 
            "type":"exact",
            "value":{ 
                "id":user_id,
                "table":"notion_user"
            }
        },
        "operator":"person_contains",
        "property":"L}(O",
        "value_type":"person"
    },{
        "id":"b6963c9a-4350-4cfc-92b7-27a4ad2c08e8",
        "type":"checkbox",
        "value":{"type": "exact", "value": False},
        "property":"X*]x",
        "comparator":"checkbox_is"
    }]


    filter_params =  {
        "filters":[ 
            { 
                "filter":{ 
                    "value":{ 
                        "type":"exact",
                        "value":{ 
                            "id":user_id,
                            "table":"notion_user"
                        }
                    },
                    "operator":"person_contains"
                },
                "property":"L}(O"
            },
            { 
                "filter":{ 
                    "value":{ 
                        "type":"exact",
                        "value":False
                    },
                    "operator":"checkbox_is"
                },
                "property":"X*]x"
            }
        ],
        "operator":"and"
    },

    return list(cv.build_query(filter=filter_params).execute())


def string_format(active_tasks):
    # if a task is unfinished, return a seedling icon
    unfinished = lambda x: '' if len(x.Status)==1 and x.Status[0] == 'done yesterday' else ':seedling:'
    # if a task is unpredicted, return a baby icon
    unpredicted = lambda x: ':baby:' if 'unplanned' in x.Tags else ''
    # initialise strings
    in_progress = ''
    done_yesterday = ''
    # stringformat every task and add it to the overview strings
    for x in active_tasks:
        url = f'https://www.notion.so/mycellhub/{x.id.replace("-", "")}'
        if 'in progress' in x.Status:
            in_progress += f'• <{url}|{x.title}> {unpredicted(x)}\n'

        if 'done yesterday' in x.Status:
            done_yesterday += f'• <{url}|{x.title}> {unfinished(x)}{unpredicted(x)}\n'
    return in_progress, done_yesterday


def message_to_slack_blocks(done_yesterday, in_progress):
    return  [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*YESTERDAY:*\n{done_yesterday}"
                },
            },{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*TODAY:*\n{in_progress}"
                },

            },{
                "type": "divider"
            },{
                "type": "context",
                "elements": [{
                                "text": "*Daily Update*  |  _:notion: integration created by Thomas Pinna_",
                                "type": "mrkdwn"
                            }]
            }]


def push_blocks_to_slack(channel, blocks): 
    #push tasks to slack
    client = slack.WebClient(token=os.environ['slack_key'])

    response = client.chat_postMessage(
        channel=channel,
        blocks=blocks,
        as_user = True
    )


if __name__ == "__main__":
    main_process(
        user_id='41d1a012-7c6f-49a3-8e80-acdcddb3c92b',
        channel='#daily_updates'
        )
