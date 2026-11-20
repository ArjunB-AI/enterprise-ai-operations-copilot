
TICKET_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_employee_ticket",
            "description": (
                "Create an IT ticket for the authenticated employee. "
                "Use this when an employee wants to report an issue "
                "or submit an IT request."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_type": {
                        "type": "string",
                        "enum": [
                            "incident",
                            "request",
                            "asset",
                            "onboarding",
                        ],
                        "description": "Type of IT ticket.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Short title of the ticket.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed explanation of the issue or request.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": [
                            "low",
                            "medium",
                            "high",
                            "critical",
                        ],
                        "description": "Ticket priority. Defaults to medium.",
                    },
                },
                "required": [
                    "ticket_type",
                    "title",
                    "description",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_tickets",
            "description": (
                "Retrieve all tickets belonging to the authenticated "
                "employee. Use this when an employee asks about their "
                "tickets or ticket statuses."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]
