/*
 *  Textures and Lighting
 *
 *  Demonstrates using lighting and textures.
 *
 *  Key bindings:
 *  l          Toggle lighting on/off
 *  t          Change textures
 *  m          Toggles texture mode modulate/replace
 *  a/A        decrease/increase ambient light
 *  d/D        decrease/increase diffuse light
 *  s/S        decrease/increase specular light
 *  e/E        decrease/increase emitted light
 *  n/N        Decrease/increase shininess
 *  []         Lower/rise light
 *  x          Toggle axes
 *  arrows     Change view angle
 *  PgDn/PgUp  Zoom in and out
 *  0          Reset view angle
 *  ESC        Exit
 */
#include "CSCIx229.h"
int mode=0;       //  Texture mode
int ntex=0;       //  Cube faces
int axes=1;       //  Display axes
int th=0;         //  Azimuth of view angle
int ph=0;         //  Elevation of view angle
int light=1;      //  Lighting
int rep=1;        //  Repitition
double asp=1;     //  Aspect ratio
double dim=3.0;   //  Size of world
// Light values
int emission  =   0;  // Emission intensity (%)
int ambient   =  30;  // Ambient intensity (%)
int diffuse   = 100;  // Diffuse intensity (%)
int specular  =   0;  // Specular intensity (%)
int shininess =   0;  // Shininess (power of two)
float shiny   =   1;    // Shininess (value)
int zh        =  90;  // Light azimuth
float ylight  =   0;  // Elevation of light
unsigned int texture[7]; // Texture names

// Other Constants
int resolution = 128;

void elementWiseSubtract(float v1[3], float v2[3], float v3[3])
{
   v3[0] = v1[0] - v2[0];
   v3[1] = v1[1] - v2[1];
   v3[2] = v1[2] - v2[2];
}

void elementWiseAdd(float v1[3], float v2[3], float v3[3])
{
   v3[0] = v1[0] + v2[0];
   v3[1] = v1[1] + v2[1];
   v3[2] = v1[2] + v2[2];
}

void normalize(float v[3])
{
   float scale = sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
   v[0] *= scale;
   v[1] *= scale;
   v[2] *= scale;
}

void crossProduct(float v1[3], float v2[3], float v3[3])
{
   v3[0] = v1[1] * v2[2] - v1[2] * v2[1];
   v3[1] = v1[2] * v2[0] - v1[0] * v2[2];
   v3[2] = v1[0] * v2[1] - v1[1] * v2[0];
}

/*
 *
 * CREDIT: Noise functions taken from https://github.com/czinn/perlin/blob/master/perlintest.c
 *
 */
double rawnoise(int n) {
    n = (n << 13) ^ n;
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0);
}

double noise2d(int x, int y, int octave, int seed) {
    return rawnoise(x * 1619 + y * 31337 + octave * 3463 + seed * 13397);
}

double interpolate(double a, double b, double x) {
    double f = (1 - cos(x * 3.141593)) * 0.5;

    return a * (1 - f) + b * f;
}

double smooth2d(double x, double y, int octave, int seed) {
    int intx = (int)x;
    double fracx = x - intx;
    int inty = (int)y;
    double fracy = y - inty;
    
    double v1 = noise2d(intx, inty, octave, seed);
    double v2 = noise2d(intx + 1, inty, octave, seed);
    double v3 = noise2d(intx, inty + 1, octave, seed);
    double v4 = noise2d(intx + 1, inty + 1, octave, seed);
    
    double i1 = interpolate(v1, v2, fracx);
    double i2 = interpolate(v3, v4, fracx);
    
    return interpolate(i1, i2, fracy);
}

double pnoise2d(double x, double y, double persistence, int octaves, int seed) {
   double total = 0.0;
   double frequency = 1.0;
   double amplitude = 1.0;
   int i = 0;
   
   for(i = 0; i < octaves; i++) {
       total += smooth2d(x * frequency, y * frequency, i, seed) * amplitude;
       frequency /= 2;
       amplitude *= persistence;
   } 

   return total;
}

/*
 * END third party noise functions
 */

static void generateHeightMap(int resolution, float heightmap[resolution][resolution])
{
   for(int x = 0; x < resolution; x++)
   {
      for(int z = 0; z < resolution; z++)
      {
         // Don't really know how these numbers work, just fiddles
         // with it until something decent appeared
         float maxFrequency = 256 / (float) resolution;
         float nx = x * maxFrequency - 0.5;
         float nz = z * maxFrequency - 0.5;

         heightmap[x][z] = pnoise2d(nx, nz, 1.4, 5, 2555) / resolution;
      }
   }
}

static void surface(double x, double y, double z, double dx, double dy, double dz, float heightmap[resolution][resolution])
{
   int verticesRes = resolution + 1;
   int numIndices = resolution * resolution * 6;
   int numVertices = verticesRes * verticesRes;
   float * vertices = malloc(numVertices * 3 * sizeof(float));
   float * textures = malloc(numVertices * 2 * sizeof(float));
   float * normals = calloc(numVertices * 3,  sizeof(float));
   int * indices = malloc(numIndices * sizeof(int));

   float squareSize = 1.0 / resolution;

   // Define the vertices and the textures
   // the x and z value are simply the coordinates of a square divided by the number of squares
   // the y is the heightmap
   for(int x = 0; x < verticesRes; x++)
   {
      for(int z = 0; z < verticesRes; z++)
      {
         float tx = x * squareSize;
         float tz = z * squareSize;
         int vertexAddr = (z * verticesRes + x) * 3;
         int textureAddr = (z * verticesRes + x) * 2;

         vertices[vertexAddr] = tx;
         vertices[vertexAddr + 1] = heightmap[x][z];
         vertices[vertexAddr + 2] = tz;

         textures[textureAddr] = tx;
         textures[textureAddr + 1] = tz;
      }
   }

   // Define each square as two triangles, both going counterclockwise
   for(int x = 0; x < resolution; x++)
   {
      for(int z = 0; z < resolution; z++)
      {
         int indexArr = (z * resolution + x) * 6;
         int vx00 = (z * verticesRes + x);
         int vx01 = vx00 + verticesRes;
         int vx10 = vx00 + 1;
         int vx11 = vx00 + verticesRes + 1; // Add verticesRes for +1 Z and for +1 x

         // First triangle
         indices[indexArr] = vx00;
         indices[indexArr + 1] = vx11;
         indices[indexArr + 2] = vx01;

         // Second triangle
         indices[indexArr + 3] = vx00;
         indices[indexArr + 4] = vx10;
         indices[indexArr + 5] = vx11;

         // Normal calculation
         float toCross1[3];
         float toCross2[3];
         float cross[3];

         // Calculate normal of first triangle
         elementWiseSubtract(&vertices[vx11*3], &vertices[vx00*3], toCross1);
         elementWiseSubtract(&vertices[vx01*3], &vertices[vx00*3], toCross2);
         crossProduct(toCross2, toCross1, cross);

         elementWiseAdd(&vertices[vx00*3], toCross1, toCross1);
         elementWiseAdd(&vertices[vx00*3], toCross2, toCross2);

         // Add the normal of the triangle to the three vertices that touch it
         elementWiseAdd(&normals[vx00*3], cross, &normals[vx00*3]);
         elementWiseAdd(&normals[vx11*3], cross, &normals[vx11*3]);
         elementWiseAdd(&normals[vx01*3], cross, &normals[vx01*3]);

         // Calculate the normal of the second triangle
         elementWiseSubtract(&vertices[vx10*3], &vertices[vx00*3], toCross1);
         elementWiseSubtract(&vertices[vx11*3], &vertices[vx00*3], toCross2);
         crossProduct(toCross2, toCross1, cross);

         elementWiseAdd(&normals[vx00*3], cross, &normals[vx00*3]);
         elementWiseAdd(&normals[vx11*3], cross, &normals[vx11*3]);
         elementWiseAdd(&normals[vx10*3], cross, &normals[vx10*3]);
      }
   }

   // glPushMatrix();
   // glTranslated(x, y, z);
   // glScaled(dx, dy, dz);
   // for(int x = 0; x < verticesRes; x++)
   // {
   //    for(int z = 0; z < verticesRes; z++)
   //    {
   //       int vertexAddr = (z * verticesRes + x) * 3;
   //       glBegin(GL_LINE_STRIP);
   //       glVertex3f(vertices[vertexAddr], vertices[vertexAddr + 1], vertices[vertexAddr + 2]);
   //       float temp[3];
   //       elementWiseAdd(&normals[vertexAddr], &vertices[vertexAddr], temp);
   //       glVertex3f(temp[0], temp[1], temp[2]);
   //       glEnd();
   //    }
   // }
   // glPopMatrix();

   glNormalPointer(GL_FLOAT, 0, normals);
   glEnableClientState(GL_NORMAL_ARRAY);

   glVertexPointer(3, GL_FLOAT, 0, vertices);
   glEnableClientState(GL_VERTEX_ARRAY);

   glTexCoordPointer(2, GL_FLOAT, 0, textures);
   glEnableClientState(GL_TEXTURE_COORD_ARRAY);

   //  Enable textures
   glEnable(GL_TEXTURE_2D);
   glDrawElements(GL_TRIANGLES, numIndices, GL_UNSIGNED_INT, indices);

   glDisableClientState(GL_TEXTURE_COORD_ARRAY);
   glDisableClientState(GL_NORMAL_ARRAY);
   glDisableClientState(GL_VERTEX_ARRAY);

   //  Undo transformations and textures
   glDisable(GL_TEXTURE_2D);

   free(indices);
   free(vertices);
   free(textures);
   free(normals);
}

static void core(double x, double y, double z, double dx, double dy, double dz, float heightmap[resolution][resolution])
{
   glEnable(GL_TEXTURE_2D);

   float height = 1;
   glBegin(GL_QUADS);
   // Draw the bottom of the box
   glNormal3f( 0,-1, 0);
   glTexCoord2f(0,0); glVertex3f(0, -height, 0);
   glTexCoord2f(1,0); glVertex3f(1, -height, 0);
   glTexCoord2f(1,1); glVertex3f(1, -height, 1);
   glTexCoord2f(0,1); glVertex3f(0, -height, 1);
   glEnd();

   // Back
   glBegin(GL_QUADS);
   glNormal3f( 0, 0, -1);
   for(int x = 0; x < resolution; x++)
   {
      float dx = 1 / (float)resolution;
      float resX = x / (float)resolution;
      glTexCoord2f(resX,0); glVertex3f(resX, -height, 0);
      glTexCoord2f(resX + dx,0); glVertex3f(resX + dx, -height, 0);
      glTexCoord2f(resX + dx, heightmap[x + 1][0] + 1); glVertex3f(resX + dx, heightmap[x + 1][0], 0);
      glTexCoord2f(resX, heightmap[x][0] + 1); glVertex3f(resX, heightmap[x][0], 0);
   }
   glEnd();

   // Front
   glBegin(GL_QUADS);
   glNormal3f( 0, 0, 1);
   for(int x = 0; x < resolution; x++)
   {
      float dx = 1 / (float)resolution;
      float resX = x / (float)resolution;
      glTexCoord2f(resX,0); glVertex3f(resX, -height, 1);
      glTexCoord2f(resX + dx,0); glVertex3f(resX + dx, -height, 1);
      glTexCoord2f(resX + dx,heightmap[x + 1][resolution] + 1); glVertex3f(resX + dx, heightmap[x + 1][resolution], 1);
      glTexCoord2f(resX,heightmap[x][resolution] + 1); glVertex3f(resX, heightmap[x][resolution], 1);
   }
   glEnd();

   // Left
   glBegin(GL_QUADS);
   glNormal3f( -1, 0, 0);
   for(int x = 0; x < resolution; x++)
   {
      float dx = 1 / (float)resolution;
      float resX = x / (float)resolution;
      glTexCoord2f(resX,0); glVertex3f(0, -height, resX);
      glTexCoord2f(resX + dx,0); glVertex3f(0, -height, resX + dx);
      glTexCoord2f(resX + dx,heightmap[0][x + 1] + 1); glVertex3f(0, heightmap[0][x + 1], resX + dx);
      glTexCoord2f(resX,heightmap[0][x] + 1); glVertex3f(0, heightmap[0][x], resX);
   }
   glEnd();

   // Right
   glBegin(GL_QUADS);
   glNormal3f( 1, 0, 0);
   for(int x = 0; x < resolution; x++)
   {
      float dx = 1 / (float)resolution;
      float resX = x / (float)resolution;
      glTexCoord2f(resX,0); glVertex3f(1, -height, resX);
      glTexCoord2f(resX + dx,0); glVertex3f(1, -height, resX + dx);
      glTexCoord2f(resX + dx,heightmap[resolution][x + 1] + 1); glVertex3f(1, heightmap[resolution][x + 1], resX + dx);
      glTexCoord2f(resX,heightmap[resolution][x] + 1); glVertex3f(1, heightmap[resolution][x], resX);
   }
   glEnd();
   glDisable(GL_TEXTURE_2D);
}

static void terrain(double x, double y, double z, double dx, double dy, double dz)
{
   //  Set specular color to white
   float white[] = {1,1,1,1};
   float Emission[]  = {0.0,0.0,0.01*emission,1.0};

   glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS,shiny);
   glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,white);
   glMaterialfv(GL_FRONT_AND_BACK,GL_EMISSION,Emission);

   if (ntex) glBindTexture(GL_TEXTURE_2D,texture[5]);

   float heightmap[resolution + 1][resolution + 1];
   generateHeightMap(resolution + 1, heightmap);
   glPushMatrix();
   glTranslated(x, y, z);
   glScaled(dx, dy, dz);
   surface(x, y, z, dx, dy, dz, heightmap);
   core(x, y, z, dx, dy, dz, heightmap);
   glPopMatrix();
}

/*
 *  Draw a ball
 *     at (x,y,z)
 *     radius r
 */
static void ball(double x,double y,double z,double r)
{
   //  Save transformation
   glPushMatrix();
   //  Offset, scale and rotate
   glTranslated(x,y,z);
   glScaled(r,r,r);
   //  White ball
   glColor3f(1,1,1);
   glutSolidSphere(1.0,16,16);
   //  Undo transofrmations
   glPopMatrix();
}

/*
 *  OpenGL (GLUT) calls this routine to display the scene
 */
void display()
{
   //  Length of axes
   const double len=2.0;
   //  Eye position
   double Ex = -2*dim*Sin(th)*Cos(ph);
   double Ey = +2*dim        *Sin(ph);
   double Ez = +2*dim*Cos(th)*Cos(ph);
   //  Erase the window and the depth buffer
   glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
   //  Enable Z-buffering in OpenGL
   glEnable(GL_DEPTH_TEST);
   //  Set perspective
   glLoadIdentity();
   gluLookAt(Ex,Ey,Ez , 0,0,0 , 0,Cos(ph),0);
   //  Light switch
   if (light)
   {
      //  Translate intensity to color vectors
      float Ambient[]   = {0.01*ambient ,0.01*ambient ,0.01*ambient ,1.0};
      float Diffuse[]   = {0.01*diffuse ,0.01*diffuse ,0.01*diffuse ,1.0};
      float Specular[]  = {0.01*specular,0.01*specular,0.01*specular,1.0};
      //  Light direction
      float Position[]  = {5*Cos(zh),ylight,5*Sin(zh),1};
      //  Draw light position as ball (still no lighting here)
      glColor3f(1,1,1);
      ball(Position[0],Position[1],Position[2] , 0.1);
      //  OpenGL should normalize normal vectors
      glEnable(GL_NORMALIZE);
      //  Enable lighting
      glEnable(GL_LIGHTING);
      //  glColor sets ambient and diffuse color materials
      glColorMaterial(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE);
      glEnable(GL_COLOR_MATERIAL);
      //  Enable light 0
      glEnable(GL_LIGHT0);
      //  Set ambient, diffuse, specular components and position of light 0
      glLightfv(GL_LIGHT0,GL_AMBIENT ,Ambient);
      glLightfv(GL_LIGHT0,GL_DIFFUSE ,Diffuse);
      glLightfv(GL_LIGHT0,GL_SPECULAR,Specular);
      glLightfv(GL_LIGHT0,GL_POSITION,Position);
   }
   else
      glDisable(GL_LIGHTING);
   //  Draw scene
   terrain(-2,0,-2 , 4,4,4);
   
   //  Draw axes - no lighting from here on
   glDisable(GL_LIGHTING);
   glColor3f(1,1,1);
   if (axes)
   {
      glBegin(GL_LINES);
      glVertex3d(0.0,0.0,0.0);
      glVertex3d(len,0.0,0.0);
      glVertex3d(0.0,0.0,0.0);
      glVertex3d(0.0,len,0.0);
      glVertex3d(0.0,0.0,0.0);
      glVertex3d(0.0,0.0,len);
      glEnd();
      //  Label axes
      glRasterPos3d(len,0.0,0.0);
      Print("X");
      glRasterPos3d(0.0,len,0.0);
      Print("Y");
      glRasterPos3d(0.0,0.0,len);
      Print("Z");
   }
   //  Display parameters
   glWindowPos2i(5,5);
   Print("Angle=%d,%d  Dim=%.1f Light=%s Texture=%s",th,ph,dim,light?"On":"Off",mode?"Replace":"Modulate");
   if (light)
   {
      glWindowPos2i(5,25);
      Print("Ambient=%d  Diffuse=%d Specular=%d Emission=%d Shininess=%.0f",ambient,diffuse,specular,emission,shiny);
   }
   //  Render the scene and make it visible
   ErrCheck("display");
   glFlush();
   glutSwapBuffers();
}

/*
 *  GLUT calls this routine when the window is resized
 */
void idle()
{
   //  Elapsed time in seconds
   double t = glutGet(GLUT_ELAPSED_TIME)/1000.0;
   zh = fmod(90*t,360.0);
   //  Tell GLUT it is necessary to redisplay the scene
   glutPostRedisplay();
}

/*
 *  GLUT calls this routine when an arrow key is pressed
 */
void special(int key,int x,int y)
{
   //  Right arrow key - increase angle by 5 degrees
   if (key == GLUT_KEY_RIGHT)
      th += 5;
   //  Left arrow key - decrease angle by 5 degrees
   else if (key == GLUT_KEY_LEFT)
      th -= 5;
   //  Up arrow key - increase elevation by 5 degrees
   else if (key == GLUT_KEY_UP)
      ph += 5;
   //  Down arrow key - decrease elevation by 5 degrees
   else if (key == GLUT_KEY_DOWN)
      ph -= 5;
   //  Keep angles to +/-360 degrees
   th %= 360;
   ph %= 360;
   //  Update projection
   Project(45,asp,dim);
   //  Tell GLUT it is necessary to redisplay the scene
   glutPostRedisplay();
}

/*
 *  GLUT calls this routine when a key is pressed
 */
void key(unsigned char ch,int x,int y)
{
   //  Exit on ESC
   if (ch == 27)
      exit(0);
   //  Reset view angle
   else if (ch == '0')
      th = ph = 0;
   //  Toggle texture mode
   else if (ch == 'm' || ch == 'M')
      mode = 1-mode;
   //  Toggle axes
   else if (ch == 'x' || ch == 'X')
      axes = 1-axes;
   //  Toggle lighting
   else if (ch == 'l' || ch == 'L')
      light = 1-light;
   //  Toggle textures mode
   else if (ch == 't')
      ntex = 1-ntex;
   //  Light elevation
   else if (ch=='[')
      ylight -= 0.1;
   else if (ch==']')
      ylight += 0.1;
   //  Ambient level
   else if (ch=='a' && ambient>0)
      ambient -= 5;
   else if (ch=='A' && ambient<100)
      ambient += 5;
   //  Diffuse level
   else if (ch=='d' && diffuse>0)
      diffuse -= 5;
   else if (ch=='D' && diffuse<100)
      diffuse += 5;
   //  Specular level
   else if (ch=='s' && specular>0)
      specular -= 5;
   else if (ch=='S' && specular<100)
      specular += 5;
   //  Emission level
   else if (ch=='e' && emission>0)
      emission -= 5;
   else if (ch=='E' && emission<100)
      emission += 5;
   //  Shininess level
   else if (ch=='n' && shininess>-1)
      shininess -= 1;
   else if (ch=='N' && shininess<7)
      shininess += 1;
   //  Repitition
   else if (ch=='+')
      rep++;
   else if (ch=='-' && rep>1)
      rep--;
   // increase dim
   else if (ch == '8')
      dim += 0.1;
   // decrease dim
   else if (ch == '9' && dim>1)
      dim -= 0.1;
   //  Translate shininess power to value (-1 => 0)
   shiny = shininess<0 ? 0 : pow(2.0,shininess);
   //  Reproject
   Project(45,asp,dim);
   //  Tell GLUT it is necessary to redisplay the scene
   glutPostRedisplay();
}

/*
 *  GLUT calls this routine when the window is resized
 */
void reshape(int width,int height)
{
   //  Ratio of the width to the height of the window
   asp = (height>0) ? (double)width/height : 1;
   //  Set the viewport to the entire window
   glViewport(0,0, width,height);
   //  Set projection
   Project(45,asp,dim);
}

/*
 *  Start up GLUT and tell it what to do
 */
int main(int argc,char* argv[])
{

   //  Initialize GLUT
   glutInit(&argc,argv);
   //  Request double buffered, true color window with Z buffering at 600x600
   glutInitDisplayMode(GLUT_RGB | GLUT_DEPTH | GLUT_DOUBLE);
   glutInitWindowSize(600,600);
   glutCreateWindow("Textures and Lighting");
   //  Set callbacks
   glutDisplayFunc(display);
   glutReshapeFunc(reshape);
   glutSpecialFunc(special);
   glutKeyboardFunc(key);
   glutIdleFunc(idle);
   //  Load textures
   texture[0] = LoadTexBMP("crate.bmp");
   texture[1] = LoadTexBMP("img1.bmp");
   texture[2] = LoadTexBMP("img2.bmp");
   texture[3] = LoadTexBMP("img3.bmp");
   texture[4] = LoadTexBMP("img4.bmp");
   texture[5] = LoadTexBMP("img5.bmp");
   texture[6] = LoadTexBMP("img6.bmp");
   //  Pass control to GLUT so it can interact with the user
   ErrCheck("init");
   glutMainLoop();
   return 0;
}
