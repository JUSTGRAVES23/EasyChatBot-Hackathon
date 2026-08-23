class MemoryPolicy:
    def can_store(self,candidate)->bool:
        return bool(candidate.value)
