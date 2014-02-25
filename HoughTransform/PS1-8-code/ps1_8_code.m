% Computation time : 27s
clear all;
IM3 = imread('ps1-input3.jpg');

% Use grayscale image to keep the more information on the image
im = rgb2gray(IM3);
G = fspecial('gaussian',10,3);
%# Filter it
Ig = imfilter(im,G,'same');
%# Display
figure(1);
% subplot(1,2,1);
 imshow(Ig)
 title('image filtered with a gaussian filter : size : 30*30, sigma=3');
 %BW = edge(Ig,'roberts',0.1);
 BW = edge(Ig,'sobel',0.03);
 %subplot(1,2,2);
 %imshow(BW);
 %title('edge detection on the filtered image: roberts');

%% Hough transform on the filtered image
% Accumulator
margin = 5;
[height,width] = size(BW);
BW2=zeros(height,width);
BW2(margin:height-margin,margin:width-margin)=BW(margin:height-margin,margin:width-margin);
BW=BW2; % removing edges on the side of the image
hough_height = sqrt(height*height+width*width);
thetamax = 180; 
threshold = 1;
H = zeros(thetamax,2*(hough_height+1));
for i=1:height
    for j=1:width
       if(BW(i,j)==threshold)
           for theta=1:thetamax
               d=round(-i*cosd(theta-1)+j*sind(theta-1)+hough_height+1); 
               % avoid negative values by adding hough_height+1
       %        if((d<=(hough_height-100) )||(d>=(hough_height+100) ))
                if(d>928 && d<948) % right pen
                    H(theta,d) = H(theta,d)+1;
                elseif((d>1000 && d<1183) && (theta>88 && theta<95)) % left pen
                    H(theta,d) = H(theta,d)+1; % vote  && d>=(hough_height-300) && d<=(hough_height+300)
               end
           end
       end
    end
end
%figure(3);
%subplot(2,2,1);
%imshow(H);
%title('Filtered image : Hough Accumulator before threshold');
bestH=max(max(H));
%threshold on the H matrix
for i=1:2*hough_height
    for j=1:thetamax
        if(H(j,i)<bestH/3.09)
            H(j,i)=0;
        else
            H(j,i)=1;
            i
        end
    end
end    
%figure(2);
%subplot(2,2,3);
%imshow(H);
%title('Filtered image : Hough Accumulator after threshold');
index_line = 1;
index_column = 1;
index_image = 1:1:width;
penwidthmax =20;
penwidthmin = 15;
%looking for lines
for theta = 2:2:thetamax
    
    for d = 1: 2*hough_height-penwidthmax
        if(theta <= 45+1 || theta >=45+90+1)
            if(H(theta,d)==threshold)
                for penwidth=penwidthmin:penwidthmax
                    if(H(theta,d+penwidth)==threshold)
                        hl(index_image,index_line) =-1*( -tand(theta-1)*index_image + (d-round(hough_height+1))/cosd(theta-1));
                        hl(index_image,index_line+1) =-1*( -tand(theta-1)*index_image + (d+penwidth-round(hough_height+1))/cosd(theta-1));
                        index_line = index_line + 2;
                        %theta
                    end
                end
            end
        else
            if(H(theta,d)==threshold)
                 for penwidth=penwidthmin:penwidthmax
                     %for distortionangle=0:1
                         if(H(theta,d+penwidth)==threshold)
                             vl(index_image,index_column) = -1*(-index_image/tand(theta-1) - (d-round(hough_height+1))/sind(theta-1));
                            vl(index_image,index_column+1) = -1*(-index_image/tand(theta-1) - (d+penwidth-round(hough_height+1))/sind(theta-1));
                            index_column = index_column +1;
                         %   theta
                      %   end
                    end
                 end
            end
        end
    end
end

% ploting lines
%figure(3);
%subplot(1,2,1)
imshow(Ig)
title('Filtered image : lines detected');
hold on;
if(index_line==1)
    if(index_column~=1)
        plot(vl,index_image,'r','LineWidth',1);
    % if index_column==1 nothing to plot
    end
    
elseif(index_column==1)
    if(index_line~=1)
          plot(index_image,hl,'r','LineWidth',1);
    % if index_line==1 nothing to plot
    end
else
     plot(index_image,hl,'r',vl,index_image,'r','LineWidth',1);
end