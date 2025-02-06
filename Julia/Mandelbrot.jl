import Pkg
Pkg.add("Images")
Pkg.add("FileIO") 
using Images, Printf

function generate_mandelbrot(width, height, max_iterations=200, x_min=-2.1, y_min=-1.2, x_max=0.6, y_max=1.2)
    img = zeros(RGB, height, width)
    
    w1, w2, w3 = 50.0, 50.0, 50.0
    p1, p2, p3 = 2.2, 2.2, 2.2
    c1, c2, c3 = 0.25, 0.5, 0.75
    
    f(x, w, p, c) = exp(-w * abs(x - c)^p)
    
    for y in 1:height
        c_im = y_min + (y_max - y_min) * (y - 1) / (height - 1)
        for x in 1:width
            c_re = x_min + (x_max - x_min) * (x - 1) / (width - 1)
            z_re, z_im = 0.0, 0.0
            iterations = 0
            
            while hypot(z_re, z_im) <= 2.0 && iterations < max_iterations
                z_re, z_im = z_re^2 - z_im^2 + c_re, 2.0 * z_re * z_im + c_im
                iterations += 1
            end
            
            c = iterations / max_iterations
            col1, col2, col3 = f(c, w1, p1, c1), f(c, w2, p2, c2), f(c, w3, p3, c3)
            img[y, x] = RGB(clamp(col1, 0, 1), clamp(col2, 0, 1), clamp(col3, 0, 1))
        end
    end
    return img
end

function measure_generation_time(width, height, repetitions=15)
    total_time = 0.0
    for i in 1:repetitions
        start_time = time()
        img = generate_mandelbrot(width, height)
        elapsed_time = (time() - start_time) * 1000 # convert to milliseconds
        println(@sprintf("Średni czas: %.2f ms", elapsed_time))
        total_time += elapsed_time
        if i == 1
            save("mandelbrot_$(width)x$(height).png", img)
        end
    end
    return total_time / repetitions
end

function main()
    sizes = [ 8192, 4096, 2048, 1024, 512, 256, 128, 64,32]
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
