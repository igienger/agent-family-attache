from fastmcp import FastMCP

mcp = FastMCP()


@mcp.tool()
def get_num_new_school_emails() -> int:
    """Gets the number of new school-reated emails."""
    return 0


if __name__ == "__main__":
    mcp.run()
