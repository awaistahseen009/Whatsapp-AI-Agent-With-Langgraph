from src.agent.tools.zoom_tools import (
    ZoomMeetingCreator,
    ZoomMeetingGetter,
    ZoomMeetingLister,
    ZoomMeetingUpdater,
    ZoomMeetingDeleter,
)
from src.agent.tools.calendar_tools import (
    CalendarEventCreator,
    CalendarEventGetter,
    CalendarEventLister,
    CalendarEventUpdater,
    CalendarEventDeleter,
)
from src.agent.tools.timezone_resolver_tools import TimezoneResolver
from src.agent.tools.db_tools.client_profile_reader import ClientProfileReader
from src.agent.tools.db_tools.client_profile_updater import ClientProfileUpdater
from src.agent.tools.db_tools.property_search import PropertySearchTool
from src.agent.tools.db_tools.property_view_logger import PropertyViewLogger
from src.agent.tools.db_tools.viewed_properties_getter import ViewedPropertiesGetter
from src.agent.tools.db_tools.meeting_logger import MeetingLogger
from src.agent.tools.db_tools.meeting_status_updater import MeetingStatusUpdater
from src.agent.tools.db_tools.meetings_getter import MeetingsGetter
from src.agent.tools.db_tools.escalation_logger import EscalationLogger
from src.agent.tools.document_search import DocumentSearchTool
from src.agent.tools.client_memory_retriever import ClientMemoryRetriever
from src.agent.tools.company_knowledge_retriever import CompanyKnowledgeRetriever
from src.agent.tools.business_hours_tool import BusinessHoursTool
from src.agent.tools.current_time_tool import CurrentTimeTool

all_tools = [
    TimezoneResolver(),
    ZoomMeetingCreator(),
    ZoomMeetingGetter(),
    ZoomMeetingLister(),
    ZoomMeetingUpdater(),
    ZoomMeetingDeleter(),
    CalendarEventCreator(),
    CalendarEventGetter(),
    CalendarEventLister(),
    CalendarEventUpdater(),
    CalendarEventDeleter(),
    ClientProfileReader(),
    ClientProfileUpdater(),
    PropertySearchTool(),
    PropertyViewLogger(),
    ViewedPropertiesGetter(),
    MeetingLogger(),
    MeetingStatusUpdater(),
    MeetingsGetter(),
    EscalationLogger(),
    DocumentSearchTool(),
    ClientMemoryRetriever(),
    CompanyKnowledgeRetriever(),
    BusinessHoursTool(),
    CurrentTimeTool(),
]