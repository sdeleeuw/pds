from tests.contacts.mcp.contact.base import ContactMCPTestCase


class ContactToolSchemaTests(ContactMCPTestCase):
    async def test_create_contact_schema_is_flat_and_closed(self):
        # Given: the registered MCP tools
        from pds.mcp.server import mcp

        # When: listing tool schemas
        tools = await mcp.list_tools()
        create = next(tool for tool in tools if tool.name == "create_contact")
        schema = create.input_schema

        # Then: writable fields are top-level and extra keys are forbidden
        properties = schema["properties"]
        self.assertIn("first_name", properties)
        self.assertIn("last_name", properties)
        self.assertIn("mobile_phone", properties)
        self.assertNotIn("payload", properties)
        self.assertNotIn("name", properties)
        self.assertNotIn("phone", properties)
        self.assertFalse(schema.get("additionalProperties", True))
