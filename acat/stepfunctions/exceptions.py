class InvalidArnError(Exception):
    def __init__(self, arn: str):
        super().__init__(f"Invalid ARN: {arn}")
        self.arn = arn
