/*
 *  Homework 3
 *
 *  Three scenes that show a complex object with different animations and transformations
 *
 *  Key bindings:
 *  m/M        Cycle through different sets of objects
 *  a          Toggle axes
 *  arrows     Change view angle
 *  z/x  Zoom in and out
 *  +/-        Changes field of view for perspective
 *  0          Reset view angle
 *  ESC        Exit
 */

/*
 * CREDIT: Isophere code largely sourced from http://www.songho.ca/opengl/gl_sphere.html
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <math.h>
//  OpenGL with prototypes for glext
#define GL_GLEXT_PROTOTYPES
#ifdef __APPLE__
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif

//  Cosine and Sine in degrees
#define Cos(x) (cos((x)*3.1415927/180))
#define Sin(x) (sin((x)*3.1415927/180))

int th=0;         //  Azimuth of view angle
int ph=0;         //  Elevation of view angle
double zh=0;      //  Rotation of teapot
int axes=1;       //  Display axes
int mode=0;       //  Projection mode

int fov=55;       //  Field of view (for perspective)
double asp=1;     //  Aspect ratio
double dim=5.0;   //  Size of world

// First person stuff
double posX = 0;
double posY = 0;
double posZ = 0;

double yaw = 0;
double pitch = 0;

/*
 *  Convenience routine to output raster text
 *  Use VARARGS to make this more flexible
 */
#define LEN 8192  //  Maximum length of text string
void Print(const char* format , ...)
{
   char    buf[LEN];
   char*   ch=buf;
   va_list args;
   //  Turn the parameters into a character string
   va_start(args,format);
   vsnprintf(buf,LEN,format,args);
   va_end(args);
   //  Display the characters one at a time at the current raster position
   while (*ch)
      glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18,*ch++);
}

void addVertices(float *vertices, int j, const float v1[3], const float v2[3], const float v3[3])
{
   vertices[j] = v1[0];
   vertices[j + 1] = v1[1];
   vertices[j + 2] = v1[2];
   vertices[j + 3] = v2[0];
   vertices[j + 4] = v2[1];
   vertices[j + 5] = v2[2];   
   vertices[j + 6] = v3[0];
   vertices[j + 7] = v3[1];
   vertices[j + 8] = v3[2];
}

void rescale(float radius, float v[3])
{
    float scale = radius / sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
    v[0] *= scale;
    v[1] *= scale;
    v[2] *= scale;
}

///////////////////////////////////////////////////////////////////////////////
// find middle point of 2 vertices
// NOTE: new vertex must be resized, so the length is equal to the radius
///////////////////////////////////////////////////////////////////////////////
// from http://www.songho.ca/opengl/gl_sphere.html
void computeHalfVertex(const float v1[3], const float v2[3], float newV[3])
{
    newV[0] = v1[0] + v2[0];    // x
    newV[1] = v1[1] + v2[1];    // y
    newV[2] = v1[2] + v2[2];    // z
    rescale(1, newV);
}

/*
 * A function that returns interesting magnitudes to make the sphere into an animated blob
 */
float wave(const float v[3])
{
   return ((1.1 + sin(v[1]) * Sin(zh)) * 0.4);
}

/*
 *  Draw icosphere
 *     size
 *     subivisions: number of times to divide the triangles from an icosahedron
 *     animation: 1 if play a weird blobby animation
 *
 * CREDIT: Isophere code largely sourced from http://www.songho.ca/opengl/gl_sphere.html
 */
static void icosphere(float s, int subdivision, int animation)
{
   //  Vertex index list
   int numIndices=60;
   const unsigned char icoIndices[] =
      {
       2, 1, 0,    3, 2, 0,    4, 3, 0,    5, 4, 0,    1, 5, 0,
      11, 6, 7,   11, 7, 8,   11, 8, 9,   11, 9,10,   11,10, 6,
       1, 2, 6,    2, 3, 7,    3, 4, 8,    4, 5, 9,    5, 1,10,
       2, 7, 6,    3, 8, 7,    4, 9, 8,    5,10, 9,    1, 6,10,
      };

   //  Vertex coordinates
   float icoVertices[] =
      {
       0.000, 0.000, 1.000,
       0.894, 0.000, 0.447,
       0.276, 0.851, 0.447,
      -0.724, 0.526, 0.447,
      -0.724,-0.526, 0.447,
       0.276,-0.851, 0.447,
       0.724, 0.526,-0.447,
      -0.276, 0.851,-0.447,
      -0.894, 0.000,-0.447,
      -0.276,-0.851,-0.447,
       0.724,-0.526,-0.447,
       0.000, 0.000,-1.000
      };

   /*
    * We define temporary indices and vertices so that we can use them dynamically as the number of triangles increases
    * with every subdivision. 
    */
   float *v1, *v2, *v3;
   float * tempVertices;
   int * tempIndices;
   float newV1[3], newV2[3], newV3[3]; // new vertex positions
   int * indices = malloc(numIndices * sizeof(int));
   float * vertices = malloc(numIndices * 3 * sizeof(float));

   // Orders the indices
   for(int i = 0; i < numIndices; i++)
   {
      indices[i] = icoIndices[i];
   }

   // Order the vertices so that the they can be rendered as triangles in order
   for(int i = 0; i < 12 * 3; i++)
   {
      vertices[i] = icoVertices[i];
   }

   // Subdivision algorithm
   for(int i = 1; i <= subdivision; i++){

      // Subdivides every triangle into 4 new triangles, so allocate 4 times the previous number of indices
      int newIndices = numIndices * 4;
      tempIndices = malloc(newIndices * sizeof(int));
      tempVertices = malloc(newIndices * 3 * sizeof(float)); // Multiply by 3 because needs 3 coords to specify a single vertex

      // Just order the indices in order
      for (int j = 0; j < newIndices; j++)
      {
         tempIndices[j] = j;
      }

      for (int j = 0; j < numIndices; j+=3)
      {
         // get 3 vertices of an existing triangle
         v1 = &vertices[indices[j] * 3];
         v2 = &vertices[indices[j + 1] * 3];
         v3 = &vertices[indices[j + 2] * 3];

         // To the halfway points in between the three edges of the triangle and get the vertex at that point
         computeHalfVertex(v1, v2, newV1);
         computeHalfVertex(v2, v3, newV2);
         computeHalfVertex(v1, v3, newV3);

         // Adds three new vertices for each one of the four triangles created from subdiving the large triangle
         // Obviously this is inefficient because we really only needs 6 vertices instead of 12, but whatever, it works
         // with no major performance problems
         int vertexStart = j * 3 * 4;
         addVertices(tempVertices, vertexStart, v1, newV1, newV3);
         addVertices(tempVertices, vertexStart + 9, newV1, v2, newV2);
         addVertices(tempVertices, vertexStart + 18, newV1, newV2, newV3);
         addVertices(tempVertices, vertexStart + 27, newV3, newV2, v3);
      }

      free(vertices);
      free(indices);
      vertices = tempVertices;
      indices = tempIndices;
      numIndices = newIndices;
   }

   // Basic rbg algorithm
   float * rgb = malloc(numIndices * 3 * sizeof(float));
   for (int i = 0; i < numIndices * 3; i++)
   {
      rgb[i] = vertices[i] * 0.5 + 0.3;
   }

   // Animation done by rescaling the vertices based on the position of each vertex
   if(animation){
      for (int i = 0; i < numIndices * 3; i+=3)
      {
         rescale(wave(&vertices[i]), &vertices[i]);
      }
   }

   //  Define vertexes
   glVertexPointer(3, GL_FLOAT, 0, vertices);
   glEnableClientState(GL_VERTEX_ARRAY);
   //  Define colors for each vertex
   glColorPointer(3,GL_FLOAT,0,rgb);
   glEnableClientState(GL_COLOR_ARRAY);
   //  Draw icosahedron
   glPushMatrix();
   glScalef(s, s, s);
   glDrawElements(GL_TRIANGLES, numIndices, GL_UNSIGNED_INT, indices);
   glPopMatrix();
   //  Disable vertex array
   glDisableClientState(GL_VERTEX_ARRAY);
   //  Disable color array
   glDisableClientState(GL_COLOR_ARRAY);
   free(vertices);
   free(indices);
   free(rgb);
}

/*
 *  Set projection
 */
static void Project()
{
   //  Tell OpenGL we want to manipulate the projection matrix
   glMatrixMode(GL_PROJECTION);
   //  Undo previous transformations
   glLoadIdentity();
   if (mode == 2)
      gluPerspective(fov,asp,dim/4,4*dim);
   //  Perspective transformation
   else if (mode == 1)
      gluPerspective(fov,asp,dim/4,4*dim);
   //  Orthogonal projection
   else
      glOrtho(-asp*dim,+asp*dim, -dim,+dim, -dim,+dim);
   //  Switch to manipulating the model matrix
   glMatrixMode(GL_MODELVIEW);
   //  Undo previous transformations
   glLoadIdentity();
}

double getZ(double th, double ph)
{
   return Cos(th)*Cos(ph);
}

double getX(double th, double ph)
{
   return -Sin(th)*Cos(ph);
}

double getY(double th, double ph)
{
   return Sin(ph);
}

/*
 * Determines the orentation depending on which perspective used
 */
void determineCameraOrientation()
{
   //  Perspective - set eye position
   if (mode == 2)
   {
      double lookX = posX - getX(yaw, pitch);
      double lookY = posY - getY(yaw, pitch);
      double lookZ = posZ - getZ(yaw, pitch);
      Print("Pos: [%f, %f, %f], Look: [%f, %f, %f]", posX, posY, posZ, lookX, lookY, lookZ);
      gluLookAt(posX, posY, posZ, lookX, lookY, lookZ, 0,Cos(pitch),0);
   }
   else if (mode == 1)
   {
      double Ex = 2*dim*getX(th, ph);
      double Ey = 2*dim*getY(th, ph);
      double Ez = 2*dim*getZ(th, ph);
      Print("Pos: [%f, %f, %f]", Ex, Ey, Ez);
      gluLookAt(Ex,Ey,Ez , 0,0,0 , 0,Cos(ph),0);
   }
   //  Orthogonal - set world orientation
   else
   {
      glRotatef(ph,1,0,0);
      glRotatef(th,0,1,0);
   }
}

/*
 *  OpenGL (GLUT) calls this routine to display the scene
 */
void display()
{
   const double len=1.5;  //  Length of axes
   //  Erase the window and the depth buffer
   glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
   //  Enable Z-buffering in OpenGL
   glEnable(GL_DEPTH_TEST);
   //  Undo previous transformations
   glLoadIdentity();
   //  Handle different perspectives
   determineCameraOrientation();

   glPushMatrix();

   // Rotate and float the entire situation
   glTranslatef(0,Cos(zh),0);
   glRotatef(zh,0,1,0);

   // Rotate each of the individual objects to where I want them.
   glPushMatrix();
   glTranslatef(0,1,0);
   icosphere(1, 3, 1);
   glPopMatrix();

   glPushMatrix();
   glTranslatef(0,-1,0);
   glRotatef(180, 1, 0, 0);
   icosphere(1, 3, 1);
   glPopMatrix();

   glPushMatrix();
   glTranslatef(1,0,0);
   glRotatef(90, 0, 0, 1);
   icosphere(1, 3, 1);
   glPopMatrix();

   glPushMatrix();
   glTranslatef(-1,0,0);
   glRotatef(-90, 0, 0, 1);
   icosphere(1, 3, 1);
   glPopMatrix();

   glPushMatrix();
   glTranslatef(0,0,1);
   glRotatef(-90, 1, 0, 0);
   icosphere(1, 3, 1);
   glPopMatrix();

   glPushMatrix();
   glTranslatef(0,0,-1);
   glRotatef(90, 1, 0, 0);
   icosphere(1, 3, 1);
   glPopMatrix();

   glPopMatrix();
   
   //  White
   glColor3f(1,1,1);
   //  Draw axes
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
   //  Five pixels from the lower left corner of the window
   glWindowPos2i(5,25);
   //  Print the text string
   // Print("Angle=%d,%d  Dim=%.1f FOV=%d Projection Mode=%d",th,ph,dim,fov,mode);
   //  Render the scene
   glFlush();
   //  Make the rendered scene visible
   glutSwapBuffers();
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
   Project();
   //  Tell GLUT it is necessary to redisplay the scene
   glutPostRedisplay();
}

void matchViewAngle()
{
   yaw = th;
   pitch = ph;
   posX = 2*dim*getX(th, ph);
   posY = 2*dim*getY(th, ph);
   posZ = 2*dim*getZ(th, ph);
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
   //  Toggle axes
   else if (ch == 'a' || ch == 'A')
      axes = 1-axes;
   //  Switch display mode
   else if (ch == 'm'){
      mode = (mode+1)%3;
      if(mode == 2){
         matchViewAngle();
      }
   }
   else if (ch == 'M'){
      mode = (mode+1)%3;
      if(mode == 2){
         matchViewAngle();
      }
   }
   //  Change field of view angle
   else if (ch == '-' && ch>1)
      fov--;
   else if (ch == '+' && ch<179)
      fov++;
   //  Change dimension
   else if (ch == 'z')
      dim += 0.1;
   else if (ch == 'x')
      dim -= 0.1;
   //  Reproject
   Project();
   //  Tell GLUT it is necessary to redisplay the scene
   glutPostRedisplay();
}

/*
 *  GLUT calls this routine when the window is resized
 */
void reshape(int width,int height)
{
   asp = (height>0) ? (double)width/height : 1;
   //  Set the viewport to the entire window
   glViewport(0,0, width,height);
   //  Set projection
   Project();
}

/*
 *  GLUT calls this toutine when there is nothing else to do
 */
void idle()
{
   double t = glutGet(GLUT_ELAPSED_TIME)/1000.0;
   zh = fmod(90*t,360);
   glutPostRedisplay();
}

/*
 *  Start up GLUT and tell it what to do
 */
int main(int argc,char* argv[])
{
   //  Initialize GLUT and process user parameters
   glutInit(&argc,argv);
   //  Request double buffered, true color window with Z buffering at 600x600
   glutInitWindowSize(600,600);
   glutInitDisplayMode(GLUT_RGB | GLUT_DEPTH | GLUT_DOUBLE);
   //  Create the window
   glutCreateWindow("Homework4_Michael_Yoshimura");
   //  Tell GLUT to call "idle" when there is nothing else to do
   glutIdleFunc(idle);
   //  Tell GLUT to call "display" when the scene should be drawn
   glutDisplayFunc(display);
   //  Tell GLUT to call "reshape" when the window is resized
   glutReshapeFunc(reshape);
   //  Tell GLUT to call "special" when an arrow key is pressed
   glutSpecialFunc(special);
   //  Tell GLUT to call "key" when a key is pressed
   glutKeyboardFunc(key);
   //  Pass control to GLUT so it can interact with the user
   glutMainLoop();
   return 0;
}
