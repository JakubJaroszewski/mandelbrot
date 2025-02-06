using Base.Threads
using Images
using Printf
using Statistics

const MAX_ITER = 200

function mandelbrot(c_re, c_im)
    z_re, z_im = 0.0, 0.0
    iterations = 0
    while z_re^2 + z_im^2 <= 4.0 && iterations < MAX_ITER
        z_re, z_im = z_re^2 - z_im^2 + c_re, 2.0 * z_re * z_im + c_im
        iterations += 1
    end
    return iterations / MAX_ITER
end

function compute_mandelbrot(image, size, start_row, end_row)
    x_min, x_max = -2.1, 0.6
    y_min, y_max = -1.2, 1.2

    w1, w2, w3 = 50.0, 50.0, 50.0
    p1, p2, p3 = 2.2, 2.2, 2.2
    c1, c2, c3 = 0.25, 0.5, 0.75
    
    f(x, w, p, c) = exp(-w * abs(x - c)^p)
    
    for y in start_row:end_row
        c_im = y_min + (y_max - y_min) * (y - 1) / (size - 1)
        for x in 1:size
            c_re = x_min + (x_max - x_min) * (x - 1) / (size - 1)
            c = mandelbrot(c_re, c_im)
            
            col1, col2, col3 = f(c, w1, p1, c1), f(c, w2, p2, c2), f(c, w3, p3, c3)
            image[y, x] = RGB(clamp(col1, 0, 1), clamp(col2, 0, 1), clamp(col3, 0, 1))
        end
    end
end

function generate_mandelbrot(size, cores)
    image = zeros(RGB, size, size)
    block_size = div(size, cores)
    
    @threads for i in 0:(cores - 1)
        start_row = i * block_size + 1
        end_row = (i == cores - 1) ? size : (i + 1) * block_size
        compute_mandelbrot(image, size, start_row, end_row)
    end
    return image
end

function measure_generation_time(width, height, repetitions)
    cores = Threads.nthreads()
    time_arr=[]
    for i in 1:repetitions
        start_time = time()
        img = generate_mandelbrot(width, cores)
        elapsed_time = (time() - start_time) * 1000
        push!(time_arr,elapsed_time)
        println(@sprintf("Średni czas: %.2f ms", elapsed_time))
        if i == 1
            save("mandelbrot_$(width)x$(height)_threds.png", img)
        end
    end
    timeArrSort = sort(time_arr)
    return  sum(timeArrSort[2:end-1]) / length(timeArrSort[2:end-1])
end

function main()
    sizes = [8192, 4096, 2048, 1024, 512, 256, 128, 64, 32]
    repetitions = 8
    open("generation_times_final.txt", "w") do writer
        for size in sizes
            avg_time = measure_generation_time(size, size, repetitions)
            println(writer, @sprintf("%dx%d; %.2f", size, size, avg_time))
            println(@sprintf("Rozmiar: %dx%d, Średni czas: %.2f ms", size, size, avg_time))
        end
    end
end

main()