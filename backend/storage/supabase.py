from backend.core.supabase import supabase_wrapper


class SupabaseConnectionManager:
    """
    Adapter delegating connection calls to the unified SupabaseWrapper.
    """

    def get_client(self):
        return supabase_wrapper.get_client()


supabase_manager = SupabaseConnectionManager()
