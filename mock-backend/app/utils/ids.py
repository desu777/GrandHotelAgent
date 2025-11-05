"""
ID generators for in-memory mock data.
Starting values match documentation examples.
"""


class IDGenerator:
    """Thread-unsafe ID generator for mock purposes."""

    def __init__(self, start: int = 1):
        """
        Initialize generator with starting ID.

        Args:
            start: Starting ID value
        """
        self.current = start

    def next(self) -> int:
        """
        Get next ID and increment counter.

        Returns:
            Next sequential ID
        """
        id_val = self.current
        self.current += 1
        return id_val


# Global ID generators matching documentation examples
reservation_id_gen = IDGenerator(start=205)
restaurant_table_id_gen = IDGenerator(start=12)
