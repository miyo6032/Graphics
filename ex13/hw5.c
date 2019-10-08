/*
 *  Lighting
 *
 *  Demonstrates Gourand shading of a blob (which is originally an isosphere)
 *
 *  CUSTOM CONTROLS:
 *  
 *  c          Toggles whether normals are drawn on the object
 *  v          Change number of subvisions of the object
 *
 *  Key bindings:
 *  l          Toggles lighting
 *  a/A        Decrease/increase ambient light
 *  d/D        Decrease/increase diffuse light
 *  s/S        Decrease/increase specular light
 *  e/E        Decrease/increase emitted light
 *  n/N        Decrease/increase shininess
 *  F1         Toggle smooth/flat shading
 *  F2         Toggle local viewer mode
 *  F3         Toggle light distance (1/5)
 *  m          Toggles light movement
 *  []         Lower/rise light
 *  p          Toggles ortogonal/perspective projection
 *  +/-        Change field of view of perspective
 *  x          Toggle axes
 *  arrows     Change view angle
 *  1/2        Zoom in and out
 *  0          Reset view angle
 *  ESC        Exit
 *
 * CREDIT: https://schneide.blog/2016/07/15/generating-an-icosphere-in-c/
 * Walked me though a different isosphere implementation that doens't duplicate its vertices
 * Because trying to calulate the lighting with gourad shading with 6 different vertices as the same
 * vertex is extremely mindbending
 */
#include "CSCIx229.h"

int axes=1;       //  Display axes
int mode=1;       //  Projection mode
int move=1;       //  Move light
int th=0;         //  Azimuth of view angle
int ph=0;         //  Elevation of view angle
int fov=55;       //  Field of view (for perspective)
int light=1;      //  Lighting
double asp=1;     //  Aspect ratio
double dim=3.0;   //  Size of world
// Light values
int one       =   1;  // Unit value
int distance  =   5;  // Light distance
int inc       =  10;  // Ball increment
int smooth    =   1;  // Smooth/Flat shading
int local     =   0;  // Local Viewer Model
int emission  =   0;  // Emission intensity (%)
int ambient   =  30;  // Ambient intensity (%)
int diffuse   = 100;  // Diffuse intensity (%)
int specular  =   0;  // Specular intensity (%)
int shininess =   0;  // Shininess (power of two)
float shiny   =   1;  // Shininess (value)
int zh        =  90;  // Light azimuth
float ylight  =   0;  // Elevation of light

// Other globals
int showNormals = 0;
int subdivisions = 4;

// Moved to a vertex because using float[3] everywhere hurt my brain
struct Vertex
{
   float x;
   float y;
   float z;
};

struct Triangle
{
   int vertices[3];
};

void rescale(float radius, struct Vertex * v)
{
    float scale = radius / sqrt(v->x*v->x + v->y*v->y + v->z*v->z);
    v->x *= scale;
    v->y *= scale;
    v->z *= scale;
}

void crossProduct(struct Vertex v1, struct Vertex v2, struct Vertex * newV)
{
   newV->x = v1.y * v2.z - v1.z * v2.y;
   newV->y = v1.z * v2.x - v1.x * v2.z;
   newV->z = v1.x * v2.y - v1.y * v2.x;
}

void elementWiseAdd(struct Vertex v1, struct Vertex v2, struct Vertex * newV)
{
   newV->x = v1.x + v2.x;
   newV->y = v1.y + v2.y;
   newV->z = v1.z + v2.z;
}

void elementWiseSubtract(struct Vertex v1, struct Vertex v2, struct Vertex * newV)
{
   newV->x = v2.x - v1.x;
   newV->y = v2.y - v1.y;
   newV->z = v2.z - v1.z;
}

// find middle point of 2 vertices
// NOTE: new vertex must be resized, so the length is equal to the radius
// from http://www.songho.ca/opengl/gl_sphere.html
void computeHalfVertex(struct Vertex v1, struct Vertex v2, struct Vertex * newV)
{
   elementWiseAdd(v1, v2, newV);
   rescale(1, newV);
}

/*
 * A function that returns interesting magnitudes to make the sphere into an animated blob
 */
float wave(struct Vertex v)
{
   return ((1.1 + sin(v.y) * cos(v.x * 2) * Sin(zh)) * 0.4);
}

/*
 * Returns the index of the vertex in the vertices array if that vertex already has been created,
 * otherwise creates that vertex, puts it in the vertices array, and return the index that it is stored at
 */
int getMidEdgeVertex(int vertex1, int vertex2, int ** vertexLookup, struct Vertex * vertices, int * verticesFilled)
{
   if(vertex1 == vertex2)
   {
      printf("lookup vertices are the same!");
      exit(1);
   }
   // Swap to make sure smaller vertex is first because
   // vertices specified the other way around should return the same vertex
   if(vertex1 > vertex2)
   {
      int t = vertex1;
      vertex1 = vertex2;
      vertex2 = t;
   }

   // If the vertex has already been created, then return
   if(vertexLookup[vertex1][vertex2] != -1)
   {
      return vertexLookup[vertex1][vertex2];
   }

   // Create the vertex, add it to the lookup, and increase the verticesFilled
   computeHalfVertex(vertices[vertex1], vertices[vertex2], &vertices[*verticesFilled]);
   vertexLookup[vertex1][vertex2] = *verticesFilled;
   (*verticesFilled)++; // Increment because we just added a new vertex (Why does C not have lists :( )
   return vertexLookup[vertex1][vertex2];
}

/*
 * Subdivides all triangles into four more triangles, creating a sphere at high enough subdivisons.
 * Sourced from https://schneide.blog/2016/07/15/generating-an-icosphere-in-c/
 */
int subdivide(struct Vertex * vertices, struct Triangle * triangles, struct Vertex * newVertices, struct Triangle * newTriangles, int numOldVertices, int numNewTriangles, int numNewVertices)
{
   int numOldTriangles = numNewTriangles / 4;
   // Initialize lookup which maps between
   // two vertices to the midpoint of that vertex
   int ** lookup = malloc(numNewVertices * sizeof(int*));
   for(int i = 0; i < numNewVertices; i++)
   {
      int * row = malloc(numNewVertices * sizeof(int));
      for(int j = 0; j < numNewVertices; j++)
      {
         row[j] = -1;
      }
      lookup[i] = row;
   }

   // Copy the existing vertices to the new vertices
   for(int i = 0; i < numOldVertices; i++)
   {
      newVertices[i] = vertices[i];
   }

   int trianglesFilled = 0;
   int verticesFilled = numOldVertices;

   // For each triangle, subdivide it
   for(int t = 0; t < numOldTriangles; t++)
   {
      int mid[3];
      for(int i = 0; i < 3; ++i)
      {
         mid[i] = getMidEdgeVertex(triangles[t].vertices[i], triangles[t].vertices[(i + 1) % 3], lookup, newVertices, &verticesFilled);
      }

      // Record the new triangles
      newTriangles[trianglesFilled].vertices[0] = triangles[t].vertices[0];
      newTriangles[trianglesFilled].vertices[1] = mid[0];
      newTriangles[trianglesFilled].vertices[2] = mid[2];

      newTriangles[trianglesFilled + 1].vertices[0] = triangles[t].vertices[1];
      newTriangles[trianglesFilled + 1].vertices[1] = mid[1];
      newTriangles[trianglesFilled + 1].vertices[2] = mid[0];

      newTriangles[trianglesFilled + 2].vertices[0] = triangles[t].vertices[2];
      newTriangles[trianglesFilled + 2].vertices[1] = mid[2];
      newTriangles[trianglesFilled + 2].vertices[2] = mid[1];

      newTriangles[trianglesFilled + 3].vertices[0] = mid[0];
      newTriangles[trianglesFilled + 3].vertices[1] = mid[1];
      newTriangles[trianglesFilled + 3].vertices[2] = mid[2];

      trianglesFilled += 4;
   }

   for(int j = 0; j < numNewVertices; j++)
   {
     free(lookup[j]);
   }
   free(lookup);

   return verticesFilled;
}

/*
 *  Draw icosphere
 *     size
 *     subivisions: number of times to divide the triangles from an icosahedron
 *     animation: 1 if play a weird blobby animation
 *     showNOrmals to display the normals as lines
 */
static void icosphere(float s, int subdivision, int animation, int showNormals)
{
   //  Vertex index list
   int numIndices=60;
   int numVertices=12;
   int numTriangles=20;

   unsigned char indices[] =
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

   // Convert the initial vertices into a Vertex[] structure array
   struct Vertex * vertices = malloc(numVertices * sizeof(struct Vertex));
   for(int i = 0; i < numVertices; i++)
   {
      vertices[i].x = icoVertices[i * 3];
      vertices[i].y = icoVertices[i * 3 + 1];
      vertices[i].z = icoVertices[i * 3 + 2];      
   }

   // Convert the indices into a Triangle[] structure array
   struct Triangle * triangles = malloc(numTriangles * sizeof(struct Triangle));
   for(int i = 0; i < numTriangles; i++)
   {
      triangles[i].vertices[0] = indices[i * 3];
      triangles[i].vertices[1] = indices[i * 3 + 1];
      triangles[i].vertices[2] = indices[i * 3 + 2];
   }

   // Does the subdivisions
   for(int division = 1; division <= subdivision; division++)
   {
      // Every triangle gets subivided into 4 more triangles, so everything is multiplied by 4 for each subdivision
      numTriangles *= 4;
      numIndices *= 4;
      int estimatedVertices = numVertices * 4; // Because I can't find the equation for this lol so I have to estimate
      struct Vertex * newVertices = malloc(estimatedVertices * sizeof(struct Vertex));
      struct Triangle * newTriangles = malloc(numTriangles * sizeof(struct Triangle));
      
      numVertices = subdivide(vertices, triangles, newVertices, newTriangles, numVertices, numTriangles, estimatedVertices);

      free(vertices);
      free(triangles);
      vertices = newVertices;
      triangles = newTriangles;
   }

   float * convertedVertices = malloc(numVertices * 3 * sizeof(float));
   int * convertedIndices = malloc(numIndices * sizeof(int));

   if(animation)
   {
      for(int i = 0; i < numVertices; i++){
         rescale(wave(vertices[i]), &vertices[i]);
      }
   }

   // Convert back from structre into flat lists to be used by OpenGL
   for(int i = 0; i < numVertices; i++)
   {
      convertedVertices[i * 3] = vertices[i].x;
      convertedVertices[i * 3 + 1] = vertices[i].y;
      convertedVertices[i * 3 + 2] = vertices[i].z;
   }

   for(int i = 0; i < numTriangles; i++)
   {
      convertedIndices[i * 3] = triangles[i].vertices[0];
      convertedIndices[i * 3 + 1] = triangles[i].vertices[1];
      convertedIndices[i * 3 + 2] = triangles[i].vertices[2];
   }

   // Calculate DA Normals using the legendary Gouraud method
   struct Vertex * normals = calloc(numVertices, sizeof(struct Vertex));
   for(int t = 0; t < numTriangles; t++)
   {
      int v1 = triangles[t].vertices[0];
      int v2 = triangles[t].vertices[1];
      int v3 = triangles[t].vertices[2];

      struct Vertex toCross1;
      struct Vertex toCross2;
      struct Vertex cross;

      // Calculate the two vectors between the three points on the triangle
      elementWiseSubtract(vertices[v2], vertices[v1], &toCross1);
      elementWiseSubtract(vertices[v3], vertices[v2], &toCross2);

      // Cross to get the face vector
      crossProduct(toCross2, toCross1, &cross);

      // Add the face vector to all the vertices normals that are part of the triangle
      elementWiseAdd(cross, normals[v1], &normals[v1]);
      elementWiseAdd(cross, normals[v2], &normals[v2]);
      elementWiseAdd(cross, normals[v3], &normals[v3]);
   }

   float * convertedNormals = malloc(numVertices * 3 * sizeof(struct Vertex));
   for(int i = 0; i < numVertices; i++)
   {
      convertedNormals[i * 3] = normals[i].x;
      convertedNormals[i * 3 + 1] = normals[i].y;
      convertedNormals[i * 3 + 2] = normals[i].z;

      if(showNormals)
      {
         glDisable(GL_LIGHTING);

         // Add the normal to the current vertex to display nicely
         struct Vertex displayNormal;
         rescale(0.05, &normals[i]);
         elementWiseAdd(vertices[i], normals[i], &displayNormal);

         glPushMatrix();
         glScalef(s, s, s);

         // Line strip from the vertex to the caluclated vertex
         glBegin(GL_LINE_STRIP);
         glVertex3f(vertices[i].x, vertices[i].y, vertices[i].z);
         glVertex3f(displayNormal.x, displayNormal.y, displayNormal.z);
         glEnd();
         glPopMatrix();
         glEnable(GL_LIGHTING);
      }
   }

   // Color the object blue
   float * rgb = malloc(numIndices * 3 * sizeof(float));
   for(int i = 0; i < numIndices; i+=3)
   {
      rgb[i] = 0.5;
      rgb[i + 1] = 0.5;
      rgb[i + 2] = 0.9;
   }
   
   free(normals);
   free(vertices);
   free(triangles);

   glNormalPointer(GL_FLOAT, 0, convertedNormals);
   glEnableClientState(GL_NORMAL_ARRAY);
   //  Define vertexes
   glVertexPointer(3, GL_FLOAT, 0, convertedVertices);
   glEnableClientState(GL_VERTEX_ARRAY);
   //  Define colors for each vertex
   glColorPointer(3,GL_FLOAT,0,rgb);
   glEnableClientState(GL_COLOR_ARRAY);
   //  Draw icosahedron
   glPushMatrix();
   glScalef(s, s, s);
   glDrawElements(GL_TRIANGLES, numIndices, GL_UNSIGNED_INT, convertedIndices);
   glPopMatrix();
   glDisableClientState(GL_NORMAL_ARRAY);
   //  Disable vertex array
   glDisableClientState(GL_VERTEX_ARRAY);
   //  Disable color array
   glDisableClientState(GL_COLOR_ARRAY);

   free(rgb);
   free(convertedNormals);
   free(convertedVertices);
   free(convertedIndices);
}

/*
 *  Draw vertex in polar coordinates with normal
 */
static void Vertex(double th,double ph)
{
   double x = Sin(th)*Cos(ph);
   double y = Cos(th)*Cos(ph);
   double z =         Sin(ph);
   //  For a sphere at the origin, the position
   //  and normal vectors are the same
   glNormal3d(x,y,z);
   glVertex3d(x,y,z);
}

/*
 *  Draw a ball
 *     at (x,y,z)
 *     radius (r)
 */
static void ball(double x,double y,double z,double r)
{
   int th,ph;
   float yellow[] = {1.0,1.0,0.0,1.0};
   float Emission[]  = {0.0,0.0,0.01*emission,1.0};
   //  Save transformation
   glPushMatrix();
   //  Offset, scale and rotate
   glTranslated(x,y,z);
   glScaled(r,r,r);
   //  White ball
   glColor3f(1,1,1);
   glMaterialf(GL_FRONT,GL_SHININESS,shiny);
   glMaterialfv(GL_FRONT,GL_SPECULAR,yellow);
   glMaterialfv(GL_FRONT,GL_EMISSION,Emission);
   //  Bands of latitude
   for (ph=-90;ph<90;ph+=inc)
   {
      glBegin(GL_QUAD_STRIP);
      for (th=0;th<=360;th+=2*inc)
      {
         Vertex(th,ph);
         Vertex(th,ph+inc);
      }
      glEnd();
   }
   //  Undo transofrmations
   glPopMatrix();
}

/*
 *  OpenGL (GLUT) calls this routine to display the scene
 */
void display()
{
   const double len=2.0;  //  Length of axes
   //  Erase the window and the depth buffer
   glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
   //  Enable Z-buffering in OpenGL
   glEnable(GL_DEPTH_TEST);

   //  Undo previous transformations
   glLoadIdentity();
   //  Perspective - set eye position
   if (mode)
   {
      double Ex = -2*dim*Sin(th)*Cos(ph);
      double Ey = +2*dim        *Sin(ph);
      double Ez = +2*dim*Cos(th)*Cos(ph);
      gluLookAt(Ex,Ey,Ez , 0,0,0 , 0,Cos(ph),0);
   }
   //  Orthogonal - set world orientation
   else
   {
      glRotatef(ph,1,0,0);
      glRotatef(th,0,1,0);
   }

   //  Flat or smooth shading
   glShadeModel(smooth ? GL_SMOOTH : GL_FLAT);

   //  Light switch
   if (light)
   {
      //  Translate intensity to color vectors
      float Ambient[]   = {0.01*ambient ,0.01*ambient ,0.01*ambient ,1.0};
      float Diffuse[]   = {0.01*diffuse ,0.01*diffuse ,0.01*diffuse ,1.0};
      float Specular[]  = {0.01*specular,0.01*specular,0.01*specular,1.0};
      //  Light position
      float Position[]  = {distance*Cos(zh),ylight,distance*Sin(zh),1.0};
      //  Draw light position as ball (still no lighting here)
      glColor3f(1,1,1);
      ball(Position[0],Position[1],Position[2] , 0.1);
      //  OpenGL should normalize normal vectors
      glEnable(GL_NORMALIZE);
      //  Enable lighting
      glEnable(GL_LIGHTING);
      //  Location of viewer for specular calculations
      glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER,local);
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
   icosphere(2, subdivisions, 1, showNormals);

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
   Print("Angle=%d,%d  Dim=%.1f FOV=%d Projection=%s Light=%s",
     th,ph,dim,fov,mode?"Perpective":"Orthogonal",light?"On":"Off");
   if (light)
   {
      glWindowPos2i(5,45);
      Print("Model=%s LocalViewer=%s Distance=%d Elevation=%.1f",smooth?"Smooth":"Flat",local?"On":"Off",distance,ylight);
      glWindowPos2i(5,25);
      Print("Ambient=%d  Diffuse=%d Specular=%d Emission=%d Shininess=%.0f",ambient,diffuse,specular,emission,shiny);
   }
   glWindowPos2i(5, 65);
   Print("Show Normals=%s, Subdivisions=%i", showNormals?"True":"False", subdivisions);

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
   //  Smooth color model
   else if (key == GLUT_KEY_F1)
      smooth = 1-smooth;
   //  Local Viewer
   else if (key == GLUT_KEY_F2)
      local = 1-local;
   else if (key == GLUT_KEY_F3)
      distance = (distance==1) ? 5 : 1;
   //  Toggle ball increment
   else if (key == GLUT_KEY_F8)
      inc = (inc==10)?3:10;
   //  Flip sign
   else if (key == GLUT_KEY_F9)
      one = -one;
   //  Keep angles to +/-360 degrees
   th %= 360;
   ph %= 360;
   //  Update projection
   Project(mode?fov:0,asp,dim);
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
   //  Toggle axes
   else if (ch == 'x' || ch == 'X')
      axes = 1-axes;
   //  Toggle lighting
   else if (ch == 'l' || ch == 'L')
      light = 1-light;
   //  Switch projection mode
   else if (ch == 'p' || ch == 'P')
      mode = 1-mode;
   //  Toggle light movement
   else if (ch == 'm' || ch == 'M')
      move = 1-move;
   //  Move light
   else if (ch == '<')
      zh += 1;
   else if (ch == '>')
      zh -= 1;
   //  Change field of view angle
   else if (ch == '-' && ch>1)
      fov--;
   else if (ch == '+' && ch<179)
      fov++;
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
   else if (ch=='c')
   {
      if(showNormals)
      {
         showNormals = 0;
      }
      else
      {
         showNormals = 1;
      }
   }
   else if (ch=='v')
   {
      subdivisions = (subdivisions + 1) % 5;
   }
   //  PageUp key - increase dim
   else if (ch == '1')
      dim += 0.1;
   //  PageDown key - decrease dim
   else if (ch == '2')
      dim -= 0.1;
   //  Translate shininess power to value (-1 => 0)
   shiny = shininess<0 ? 0 : pow(2.0,shininess);
   //  Reproject
   Project(mode?fov:0,asp,dim);
   //  Animate if requested
   glutIdleFunc(move?idle:NULL);
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
   Project(mode?fov:0,asp,dim);
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
   glutInitWindowSize(400,400);
   glutCreateWindow("Lighting");
   //  Set callbacks
   glutDisplayFunc(display);
   glutReshapeFunc(reshape);
   glutSpecialFunc(special);
   glutKeyboardFunc(key);
   glutIdleFunc(idle);
   //  Pass control to GLUT so it can interact with the user
   ErrCheck("init");
   glutMainLoop();
   return 0;
}
