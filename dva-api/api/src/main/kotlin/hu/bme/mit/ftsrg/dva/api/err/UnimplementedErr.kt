package hu.bme.mit.ftsrg.dva.api.err

object UnimplementedErr : Exception("This feature has not been implemented yet") {
    private fun readResolve(): Any = UnimplementedErr
}