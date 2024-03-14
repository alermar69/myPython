def approximate_pi(int n):
    cdef float step
    cdef float result
    cdef float x
    step = 1.0 / n
    result = 0.0
    for i in range(n):
        x = (i + 0.5) * step
        result += 4.0 / (1.0 + x * x)

    return step * result